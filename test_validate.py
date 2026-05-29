import json
from jsonschema import validate, Draft7Validator
from pathlib import Path

schema = json.loads(Path("/Users/ooharayukio/ai-vector-ui-generator/schema/ui_asset.schema.json").read_text())
layer = {'id': 'pt_text', 'shape': 'text', 'role': 'text', 'rect': {'x': 20, 'y': 30, 'width': 300, 'height': 40}, 'text': {'value': '12,500 pt', 'font': 'main', 'size': 32, 'maxLines': 1, 'overflow': 'clip', 'fit': 'none', 'align': 'left'}, 'style': {'fill': 'theme.colors.textGold'}}

text_schema = {"$ref": "#/definitions/textLayer"}
# Resolve ref for simplicity in python validator, or just validate using jsonschema API properly
text_schema.update(schema)

v = Draft7Validator(schema["definitions"]["textLayer"])
# wait, definitions is part of schema. 
# actually it's easier to just use validate() directly with a wrapping schema

wrapper_schema = {
    "definitions": schema.get("definitions", {}),
    "$ref": "#/definitions/textLayer"
}

errors = sorted(Draft7Validator(wrapper_schema).iter_errors(layer), key=lambda e: str(e.path))
if not errors:
    print("Valid!")
for error in errors:
    print(error.message)

