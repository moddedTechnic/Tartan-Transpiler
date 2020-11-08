import * as vscode from 'vscode'

const logger = vscode.window.createOutputChannel('Tartan')

export function activate() {
	logger.appendLine('Activating Tartan')
}
