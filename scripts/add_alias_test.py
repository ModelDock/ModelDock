with open('tests/test_core.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'if __name__ == "__main__":'

new_test = '''def test_model_alias_management():
    """Verify that model alias can be set, retrieved, and affects list_models."""
    engine = EngineManager()
    models = engine.list_installed_models()
    assert len(models) > 0
    test_model = models[0]["name"]

    # 1. Set custom alias
    res = engine.set_model_alias(test_model, "Super Test AI")
    assert res["success"] is True
    assert res["alias"] == "Super Test AI"

    # 2. Verify list_installed_models reflects the alias
    updated = engine.list_installed_models()
    matching = next(m for m in updated if m["name"] == test_model)
    assert matching["alias"] == "Super Test AI"
    assert matching["display_name"] == "Super Test AI"

    # 3. Clean up / revert alias to default
    res_clear = engine.set_model_alias(test_model, "")
    assert res_clear["success"] is True
    reverted = engine.list_installed_models()
    reverted_m = next(m for m in reverted if m["name"] == test_model)
    assert reverted_m["alias"] == ""
    assert reverted_m["display_name"] == test_model
    print("\\n[Test] Model alias successfully set, verified in listing, and reverted to default.")


if __name__ == "__main__":'''

text = text.replace(target, new_test, 1)

with open('tests/test_core.py', 'w', encoding='utf-8', newline='') as f:
    f.write(text)

print("Added test_model_alias_management to tests/test_core.py")
