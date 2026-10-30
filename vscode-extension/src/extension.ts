import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
    const output = vscode.window.createOutputChannel('EZ8 Native Output');
    const children = new Set<cp.ChildProcess>();
    context.subscriptions.push(output, { dispose: () => {
        for (const child of children) { child.kill(); }
    }});
    function run(args: string[], resource?: vscode.Uri) {
        if (!vscode.workspace.isTrusted) {
            void vscode.window.showErrorMessage('Trust this workspace before running EZ8 tools.');
            return;
        }
        const executable = vscode.workspace.getConfiguration('ez8', resource).get<string>('toolPath', 'ez8');
        const folder = resource ? vscode.workspace.getWorkspaceFolder(resource) : vscode.workspace.workspaceFolders?.[0];
        output.show(true);
        output.appendLine(`[EZ8] ${executable} ${args.map(arg => JSON.stringify(arg)).join(' ')}`);
        let child: cp.ChildProcess;
        try {
            child = cp.spawn(executable, args, { cwd: folder?.uri.fsPath, shell: false });
        } catch (error) {
            output.appendLine(`[ERROR] ${String(error)}`);
            return;
        }
        children.add(child);
        child.stdout?.on('data', data => output.append(String(data)));
        child.stderr?.on('data', data => output.append(String(data)));
        child.on('error', error => {
            output.appendLine(`[ERROR] ${error.message}`);
            void vscode.window.showErrorMessage(`Cannot run EZ8: ${error.message}. Install the toolchain or configure ez8.toolPath.`);
        });
        child.on('close', (code, signal) => {
            children.delete(child);
            output.appendLine(`[EZ8] Exited: ${signal ?? code}`);
        });
    }
    context.subscriptions.push(vscode.commands.registerCommand('ez8.runTool', () => run(['--help'])));
    context.subscriptions.push(vscode.commands.registerCommand('ez8.assembleFile', async () => {
        if (!vscode.workspace.isTrusted) {
            void vscode.window.showErrorMessage('Trust this workspace before running EZ8 tools.');
            return;
        }
        const document = vscode.window.activeTextEditor?.document;
        if (!document || document.uri.scheme !== 'file') {
            void vscode.window.showErrorMessage('Open a local assembly file first.');
            return;
        }
        if (document.isDirty && !await document.save()) { return; }
        const source = document.uri.fsPath;
        const parsed = path.parse(source);
        const destination = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file(path.join(parsed.dir, `${parsed.name}.hex`)),
            filters: { 'Intel HEX': ['hex'] }, saveLabel: 'Assemble to HEX'
        });
        if (!destination) { return; }
        if (destination.scheme !== 'file' || destination.fsPath === source) {
            void vscode.window.showErrorMessage('Choose a local output file different from the source.');
            return;
        }
        run(['asm', source, '-o', destination.fsPath], document.uri);
    }));
}
export function deactivate() {}
