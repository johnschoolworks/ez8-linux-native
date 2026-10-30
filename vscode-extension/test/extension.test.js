const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const { EventEmitter } = require('node:events');

function harness(options = {}) {
    const commands = new Map(), calls = [], errors = [], lines = [];
    const child = new EventEmitter();
    child.stdout = new EventEmitter(); child.stderr = new EventEmitter(); child.kill = () => {};
    const uri = value => ({ scheme: 'file', fsPath: value });
    const vscode = {
        Uri: { file: uri },
        commands: { registerCommand: (name, callback) => { commands.set(name, callback); return { dispose() {} }; } },
        workspace: {
            isTrusted: options.trusted !== false,
            workspaceFolders: [{ uri: uri('/workspace') }],
            getWorkspaceFolder: () => ({ uri: uri('/workspace') }),
            getConfiguration: () => ({ get: () => options.executable || 'ez8' })
        },
        window: {
            activeTextEditor: options.noEditor ? undefined : { document: {
                uri: uri('/workspace/source with spaces.asm'), isDirty: !!options.dirty,
                save: async () => options.saved !== false
            } },
            showSaveDialog: async () => options.cancel ? undefined : uri(options.destination || '/workspace/output with spaces.hex'),
            createOutputChannel: () => ({ show() {}, append: x => lines.push(x), appendLine: x => lines.push(x), dispose() {} }),
            showErrorMessage: message => { errors.push(message); return Promise.resolve(); }
        }
    };
    const module = { exports: {} };
    const context = { module, exports: module.exports, require(name) {
        if (name === 'vscode') return vscode;
        if (name === 'child_process') return { spawn: (...args) => { calls.push(args); return child; } };
        return require(name);
    }};
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../out/extension.js'), 'utf8'), context);
    module.exports.activate({ subscriptions: [] });
    return { commands, calls, errors, lines, child };
}

test('help uses configured executable and no shell', () => {
    const h = harness({ executable: '/tools with spaces/ez8' });
    h.commands.get('ez8.runTool')();
    assert.equal(h.calls[0][0], '/tools with spaces/ez8');
    assert.equal(JSON.stringify(h.calls[0][1]), '["--help"]');
    assert.equal(h.calls[0][2].shell, false);
});
test('assembly preserves source/output paths as individual arguments', async () => {
    const h = harness(); await h.commands.get('ez8.assembleFile')();
    assert.equal(JSON.stringify(h.calls[0][1]), JSON.stringify(['asm', '/workspace/source with spaces.asm', '-o', '/workspace/output with spaces.hex']));
});
for (const options of [{ trusted: false }, { cancel: true }, { noEditor: true }, { dirty: true, saved: false }, { destination: '/workspace/source with spaces.asm' }]) {
    test(`does not spawn for ${JSON.stringify(options)}`, async () => {
        const h = harness(options); await h.commands.get('ez8.assembleFile')(); assert.equal(h.calls.length, 0);
    });
}
test('missing executable is handled without an unhandled error event', () => {
    const h = harness(); h.commands.get('ez8.runTool')();
    h.child.emit('error', new Error('ENOENT'));
    assert.match(h.errors[0], /ez8.toolPath/);
});
