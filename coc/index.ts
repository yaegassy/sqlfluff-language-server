import { ExtensionContext, LanguageClient, LanguageClientOptions, workspace, ServerOptions, Thenable } from 'coc.nvim';

import net from 'net';

import which from 'which';

let client: LanguageClient;

function getClientOptions(): LanguageClientOptions {
  return {
    documentSelector: [{ scheme: 'file', language: 'sql' }],
    outputChannelName: 'sqlfluff-language-server',
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher('**/.clientrc'),
    },
  };
}

function startLangServerTCP(addr: number): LanguageClient {
  const serverOptions: ServerOptions = () => {
    return new Promise((resolve /*, reject */) => {
      const clientSocket = new net.Socket();
      clientSocket.connect(addr, '127.0.0.1', () => {
        resolve({
          reader: clientSocket,
          writer: clientSocket,
        });
      });
    });
  };

  return new LanguageClient(`tcp lang server (port ${addr})`, serverOptions, getClientOptions());
}

function startLangServer(command: string, args: string[], cwd: string): LanguageClient {
  const serverOptions: ServerOptions = {
    command,
    args,
    options: { cwd },
  };

  return new LanguageClient('sqlfluff-language-server', 'sqlfluff-language-server', serverOptions, getClientOptions());
}

export async function activate(context: ExtensionContext): Promise<void> {
  const extensionConfig = workspace.getConfiguration('sqlfluff-ls');
  const isEnable = extensionConfig.get<boolean>('enable', true);
  if (!isEnable) return;

  const connectionMode = extensionConfig.get<string>('connectionMode', 'stdio');
  const isVerbose = extensionConfig.get<boolean>('verbose', false);

  if (connectionMode === 'tcp') {
    client = startLangServerTCP(2087);
  } else {
    let sqlfluffLsPath = extensionConfig.get('commandPath', '');

    if (!sqlfluffLsPath) {
      const whichSqlFluffLsCmd = whichCmd('sqlfluff-language-server');
      if (whichSqlFluffLsCmd) {
        sqlfluffLsPath = whichSqlFluffLsCmd;
      }
    }

    const commandArgs = [];
    if (isVerbose) {
      commandArgs.push('-v');
    }

    if (sqlfluffLsPath) {
      client = startLangServer(sqlfluffLsPath, commandArgs, workspace.cwd);
    }
  }

  if (client) {
    context.subscriptions.push(client.start());
  }
}

export function deactivate(): Thenable<void> {
  return client ? client.stop() : Promise.resolve();
}

function whichCmd(cmd: string): string {
  try {
    return which.sync(cmd);
  } catch (error) {
    return '';
  }
}
