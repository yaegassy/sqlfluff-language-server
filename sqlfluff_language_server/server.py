from typing import List, Optional

from pygls.lsp.methods import (
    CODE_ACTION,
    FORMATTING,
    INITIALIZE,
    INITIALIZED,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
)
from pygls.lsp.types import (
    ConfigurationItem,
    ConfigurationParams,
    DidOpenTextDocumentParams,
    Position,
    Range,
)
from pygls.lsp.types.basic_structures import (
    Diagnostic,
    DiagnosticSeverity,
    TextEdit,
    WorkspaceEdit,
)
from pygls.lsp.types.general_messages import InitializeParams, InitializedParams
from pygls.lsp.types.language_features.code_action import (
    CodeAction,
    CodeActionKind,
    CodeActionOptions,
    CodeActionParams,
)
from pygls.lsp.types.language_features.formatting import DocumentFormattingParams
from pygls.lsp.types.workspace import DidChangeTextDocumentParams
from pygls.server import LanguageServer
from sqlfluff.core.config import FluffConfig
from sqlfluff.core.linter import Linter


class SqlFluffLanguageServer(LanguageServer):
    CONFIGURATION_SECTION = "sqlfluff-ls"

    server_config = {}
    fluff_config_object: FluffConfig

    def __init__(self):
        super().__init__()


sqlfluff_server = SqlFluffLanguageServer()


def _validate(ls: SqlFluffLanguageServer, params):
    text_doc = ls.workspace.get_document(params.text_document.uri)
    source = text_doc.source
    diagnostics = _validate_sqlfluff(ls, source) if source else []
    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_sqlfluff(ls: SqlFluffLanguageServer, source: str):
    diagnostics = []

    cfg = ls.fluff_config_object
    result = Linter(cfg).lint_string_wrapped(source)
    result_records = result.as_records()
    if result_records:
        for r in result_records[0]["violations"]:
            msg = r["description"]
            col = r["line_pos"]
            line = r["line_no"]
            code = r["code"]

            d = Diagnostic(
                range=Range(
                    start=Position(line=line - 1, character=col - 1),
                    end=Position(line=line - 1, character=col),
                ),
                message=msg,
                source="sqlfluff-ls",
                code=code,
                severity=DiagnosticSeverity.Error,
            )

            diagnostics.append(d)

    return diagnostics


@sqlfluff_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: SqlFluffLanguageServer, params: DidChangeTextDocumentParams):
    _validate(ls, params)


@sqlfluff_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: SqlFluffLanguageServer, params: DidOpenTextDocumentParams):
    _validate(ls, params)


def _formatting(
    ls: SqlFluffLanguageServer, uri: str, range_: Range = None
) -> Optional[List[TextEdit]]:

    result = None

    text_doc = ls.workspace.get_document(uri)
    source = text_doc.source

    end_position_line = len(text_doc.lines) - 1
    end_position_character = len(text_doc.lines[len(text_doc.lines) - 1])

    cfg = ls.fluff_config_object

    formatted_text = ""
    try:
        lint_result = Linter(cfg).lint_string_wrapped(source, fix=True)
        formatted_text = lint_result.paths[0].files[0].fix_string()[0]
        ls.show_message_log("Formatting success")
    except Exception as e:
        ls.show_message_log("Formatting error: {}".format(e))

    if formatted_text:
        result = [
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(
                        line=end_position_line, character=end_position_character
                    ),
                ),
                new_text=str(formatted_text),
            )
        ]

    # [TextEdit] or None
    return result


@sqlfluff_server.feature(FORMATTING)
def formatting(
    ls: SqlFluffLanguageServer, params: DocumentFormattingParams
) -> Optional[List[TextEdit]]:
    return _formatting(ls, params.text_document.uri)


@sqlfluff_server.feature(
    CODE_ACTION,
    CodeActionOptions(
        code_action_kinds=[
            CodeActionKind.RefactorInline,
            CodeActionKind.RefactorExtract,
        ]
    ),
)
def code_action(
    ls: SqlFluffLanguageServer, params: CodeActionParams
) -> Optional[List[CodeAction]]:
    code_actions = []

    if (
        params.range.start.line == params.range.end.line
        and params.range.start.character == 0
        and len(params.context.diagnostics) > 0
    ):
        text_doc = ls.workspace.get_document(params.text_document.uri)
        current_content = text_doc.lines[params.range.start.line]

        noqa_content = current_content.rstrip() + " -- noqa"
        noqa_disable_all_content = current_content.rstrip() + " -- noqa: disable=all"
        noqa_enable_all_content = current_content.rstrip() + " -- noqa: enable=all"

        noqa_edit = TextEdit(range=params.range, new_text=noqa_content)
        noqa_disable_all_edit = TextEdit(
            range=params.range, new_text=noqa_disable_all_content
        )
        noqa_enable_all_edit = TextEdit(
            range=params.range, new_text=noqa_enable_all_content
        )

        code_actions.append(
            CodeAction(
                title="Ignoring Errors for current line (-- noqa)",
                kind=CodeActionKind.RefactorInline,
                edit=WorkspaceEdit(changes={params.text_document.uri: [noqa_edit]}),
            ),
        )

        code_actions.append(
            CodeAction(
                title="Ignoring Errors for current line (-- noqa: disable=all)",
                kind=CodeActionKind.RefactorInline,
                edit=WorkspaceEdit(
                    changes={params.text_document.uri: [noqa_disable_all_edit]}
                ),
            ),
        )

        code_actions.append(
            CodeAction(
                title="Ignoring Errors for current line (-- noqa: enable=all)",
                kind=CodeActionKind.RefactorInline,
                edit=WorkspaceEdit(
                    changes={params.text_document.uri: [noqa_enable_all_edit]}
                ),
            ),
        )

        return code_actions

    return None


@sqlfluff_server.feature(INITIALIZE)
async def initialize(ls: SqlFluffLanguageServer, params: InitializeParams):
    ls.fluff_config_object = FluffConfig.from_root()
    ls.show_message_log("initialize!")


@sqlfluff_server.feature(INITIALIZED)
async def initialized(ls: SqlFluffLanguageServer, params: InitializedParams):
    config_params = ConfigurationParams(
        items=[
            ConfigurationItem(section=SqlFluffLanguageServer.CONFIGURATION_SECTION),
        ]
    )
    config_items = await ls.get_configuration_async(config_params)
    server_config: dict = config_items[0]

    # ---- config sample ----
    # if "dummyKey" not in config_items[0]:
    #     server_config.update({"dummyKey": "dummyValue"})

    ls.server_config = server_config
    ls.show_message_log("initialized: {}".format(ls.server_config))
