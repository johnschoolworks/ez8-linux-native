# G2.5 — ENCORE! RS-232 Serial Smart Cable Protocol Evidence

| Field | Value |
|---|---|
| Document ID | G2.5-D48-PROTOCOL |
| Revision | 1.0 — static evidence baseline |
| Status | Static reverse engineering; **hardware protocol unverified** |
| Target cable | ENCORE! RS-232 Serial Smart Cable, P/N `00C0042-001`, rev `06.04.03` |
| Target MCU | Z8F0822 (board-specific hardware connection not exercised) |
| Companion | `g2.5-d48-architecture.md` |

## 1. Evidence scope and provenance

The findings below are from bounded, read-only examination of the ZDS II 5.6.3 `nxEz8serialSC.dll`, configuration files, and host enumeration. No serial port was opened, no request was transmitted, and no target state was measured.

- DLL path on audit host: `~/Projects/zilog-zds2-5.6.3-analysis/app/bin/nxEz8serialSC.dll`.
- DLL SHA-256: `787fb7c4b80de95066c3da6bffc9ad1cf0cbea319cb78b01c9a2ed2ffe78a42c`.
- PE32 i386, image base `0x10000000`, 352,256 bytes.
- ZDS II 5.6.3 archive SHA-256: `6ccd9e71687966a440d7519cbe246a7a1703a67045550ba76627f3453b724d0a`.
- ZDS II 5.7.0 distribution contained USB/Ethernet DLLs but not this serial DLL in the inspected package.
- `encore_tools.ini` references `NxSerial = NxEz8SerialSC.dll`, `Serial Driver = icebox:serial:serial`; `SerialSmartCable.xdt` specifies serial/COM1 and **57600 baud**. This is `CONFIGURED` evidence, not proof that the runtime initialization argument always equals 57600.

### 1.1 Host enumeration (G2.5-D2)

Host audit file: `build/g2.5/transport-audit.json`, recorded with `status=HOST_CAPABILITY_ONLY` and `gate=G2.5-D2`.

- Linux kernel `7.0.0-38-generic`; pyserial `3.5`.
- FTDI UC232R: VID/PID `0403:6001`, serial `REDACTED`, enumerated as `/dev/ttyUSB0`.
- `host_protocol=UNVERIFIED`; `target_connection=UNVERIFIED`.
- Audit booleans: `serial_port_opened=false`, `commands_sent=false`, `flash_modified=false`.

These are observations of the audit state at its timestamp, not guarantees about all future system activity.

## 2. DLL API and transport findings (`STATIC_DLL`)

Exports include `nx_Open`, `nx_Close`, `nx_Control`, `nx_ReadMem`, `nx_WriteMem`, `nx_GetEvent`, `nx_SetEvent`, `nx_ClearEvent`, `nx_GetLastError`, `sendAlgorithm`, `zGetDllInfo`, and `zGetVersionString`.

The DLL uses Win32 `CreateFileA`, `ReadFile`, `WriteFile`, `GetCommState`, `SetCommState`, `SetCommTimeouts`, `ClearCommError`, `EscapeCommFunction`, and `Sleep`. The COM device name is built from `COM` and a decimal port number. A single Win32 I/O chunk is capped at `0x1000` (4096) bytes; this is **not** evidence of a cable packet size. Write logic includes a CTS-hold check and a 5000 ms wait path. Error 995 (`ERROR_OPERATION_ABORTED`) has a read-retry/reconfiguration path.

| Routine | Address | Evidence |
|---|---|---|
| Serial write wrapper | `0x100272B0` | `thiscall`-like `ECX=self`, stack `buffer`, `length`; returns with `ret 8`. |
| Win32 `WriteFile` call | `0x100274A6` | Buffer and bounded count forwarded to Windows API. |
| Serial read wrapper | `0x10027790` | Same two stack-argument layout; `ret 8`. |
| Win32 `ReadFile` call | `0x10027874` | Caller-provided buffer and bounded count. |
| Cable identity candidate | `0x1002A780` | One-byte write, six-byte requested read, signature comparison. |
| Cable-side baud candidate | `0x1002A840` | Three-byte buffer from a divisor lookup table. |
| Windows host baud setter | `0x10028360` | DCB read/compare/update, with `SetCommState` only when baud differs. |

The wrapper calling convention is supported by disassembly, but no wire capture is available.

## 3. Candidate identity exchange (`STATIC_DLL`, not hardware-verified)

At `0x1002A780`, the DLL prepares one byte `0x80`, calls the serial write wrapper with length 1, then requests six bytes from the serial read wrapper. On a successful read, it compares response offsets 3, 4, 5 with constants at `0x10040730..32`:

```text
TX candidate: 80
RX requested: 6 bytes
RX signature: ?? ?? ?? 55 88 11
                    ^  ^  ^
                 offsets 3–5
```

The first three bytes are used for a logging/information path; their meaning is **unknown**. The exact semantics of a short read, timing, and response origin remain unverified. The routine returns nonzero only when its successful-read and signature conditions are satisfied in the analyzed branch. The label *identity* is a functional inference, not a documented vendor opcode name.

## 4. Candidate cable-side baud command (`STATIC_DLL`)

### 4.1 Calculation

`0x1002A840` multiplies runtime global `DWORD [0x1004DF3C]` by `0x1B4E81B5`, takes the high 32 bits, shifts right by 10, then subtracts one:

```text
index = (((0x1B4E81B5 * baud) >> 32) >> 10) - 1
```

It reads two table bytes at `0x10040710 + index*2` and `0x10040711 + index*2`, then constructs a three-byte write buffer with fixed byte 0 and the lookup pair in high-byte/low-byte order. There is no demonstrated range check on the computed index in this bounded disassembly; do not apply the formula to arbitrary inputs without validation.

| Baud input | Index | Table bytes (low, high) | Candidate transmitted bytes |
|---:|---:|---|---|
| 9600 | 0 | `78 00` | `00 00 78` |
| 19200 | 1 | `3C 00` | `00 00 3C` |
| 38400 | 3 | `1E 00` | `00 00 1E` |
| **57600** | **5** | **`14 00`** | **`00 00 14`** |
| 115200 | 11 | `0A 00` | `00 00 0A` |

These are static calculations for the observed table, not validated supported rates. The values correspond numerically to `1,152,000 / baud` for these examples; the physical clock or divider meaning is `INFERRED`, not verified.

### 4.2 Call sequence

The function pushes length 3, constructs the stack-resident buffer, passes its pointer to `0x100272B0`, and on successful write calls `Sleep(300)` before returning success. The byte sequence for runtime baud 57600 is therefore **candidate `00 00 14`**. No immediate cable response read was identified inside this routine.

## 5. Conditional initialization order (`STATIC_DLL`)

In the branch following a nonzero result from `0x1002A780`:

1. `0x10029BC9`: invoke candidate identity routine.
2. `0x10029C03`: configure COM timeouts (`SetCommTimeouts` path).
3. `0x10029C1B`: send cable-side baud command.
4. `0x1002A88E`: on successful write, `Sleep(300)`.
5. `0x10029C35`: invoke host-side baud setter `0x10028360`.

The timeouts supplied in this branch are five DWORDs `[5000, 1, 5000, 0, 5000]`. A separate read error-995 recovery path temporarily uses `[1000, 1, 1000, 0, 1000]`; these are distinct contexts. The host baud setter obtains the DCB, compares the current baud to the requested value, and calls `SetCommState` if different. A global word at `0x1004DEFA` is assigned `0x01E9` (489) in this branch; its meaning is unknown.

**Branch limitation:** when the identity routine returns zero, execution jumps to `0x10029C3F`, an alternate path not fully analyzed. Do not claim this is the only initialization sequence.

**Runtime limitation:** `0x1004DF3C` receives a value from an initialization structure (`[esi+8]` near `0x10029735–0x1002974B`). Although XDT specifies 57600, the complete propagation from configuration to runtime structure has not been established.

## 6. Cable protocol versus target OCD

These are separate layers:

- **Cable host protocol:** serial commands such as candidate `80` and `00 00 14` sent between host and RS-232 Smart Cable.
- **Target Z8 OCD protocol:** MCU debug operations described by target algorithm files. Observed target OCD opcodes include READID `0x00`, READ_STATUS `0x02`, WRITE_CTRL_REG `0x04`; these must **not** be mistaken for Smart Cable serial packet opcodes.

The inspected `F08X_eval_algo.ini` contains target reset and flash-control sequences, including WRITE_CTRL_REG `0x04 0x81`, flash unlock values `0x73` and `0x8C`, page erase `0x95`, and mass erase `0x63`. Consequently, a debugger connection or nominal read workflow must not be assumed safe for the MCU. No target operations are authorized in D48.

## 7. Evidence matrix and unknowns

| Claim | Class | Confidence / limitation |
|---|---|---|
| FTDI UC232R enumerated | `HOST_OBSERVED` | Host-side only. |
| Smart Cable identity and revision | `HOST_OBSERVED` | Based on physical identification supplied in audit. |
| 57600 in XDT | `CONFIGURED` | Runtime use not conclusively traced. |
| `80` one-byte request, six-byte read | `STATIC_DLL` | Not wire-captured. |
| `55 88 11` at response offsets 3–5 | `STATIC_DLL` | Not wire-captured. |
| `00 00 14` for runtime 57600 | `STATIC_DLL` | Not wire-captured; conditional branch. |
| Divisor physical meaning | `INFERRED` | Formula fits examples; oscillator source unknown. |
| DTR/RTS requirements and exact sequence | `UNVERIFIED` | API usage found; full semantics not mapped. |
| Complete framing / checksums / command set | `UNVERIFIED` | Not recovered. |
| Real hardware link and target behavior | `UNVERIFIED` | No I/O or MCU operations performed. |
| Any `HARDWARE_VERIFIED` protocol transaction | None | Explicitly absent. |

## 8. Safety and next-stage handoff

The only permitted D49 work, if separately authorized, is a Mock-only implementation of these candidate encoders, response validators, state transitions, and fail-closed safety tests. No `serial.Serial(...)`, `open('/dev/ttyUSB0', ...)`, target reset, flash unlock, erase, or programming. Do not infer hardware success from Mock test success.

D48 documentation authorization does not itself authorize D49 implementation or a formal Git freeze. Preserve `?? tools/`, the original DLL, and G2.4 files. Formal repository freeze requires separate placement/review and a verified Git state.
