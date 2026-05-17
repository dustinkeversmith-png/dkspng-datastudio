import sys
content = open('app/operations/atomic/basic_operations.py', 'r', encoding='utf-8').read()
content = content.replace(
    'df = select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))',
    'df = context.params.get("df") if context.params.get("df") is not None else select_source_dataframe(context.source, context.source_key, limit=context.params.get("limit"))'
)
open('app/operations/atomic/basic_operations.py', 'w', encoding='utf-8').write(content)
