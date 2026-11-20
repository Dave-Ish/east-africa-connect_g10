"""Run with: python -m pytest tests/"""
from ui import main_menu


def run_with_inputs(monkeypatch, capsys, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _="": next(it))
    monkeypatch.setattr("ui.terminal.clear_screen", lambda: None)
    main_menu.run_app()
    return capsys.readouterr().out


def test_exit_from_main_menu(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["0"])
    assert "Goodbye" in out


def test_invalid_input_does_not_crash(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["abc", "", "99", "0"])
    assert out.count("Invalid choice") == 3


def test_student_flow_and_return(monkeypatch, capsys):
    out = run_with_inputs(
        monkeypatch, capsys, ["1", "1", "", "2", "", "3", "", "0", "0"]
    )
    assert "STUDENT MENU" in out and "Goodbye" in out


def test_teacher_flow_and_return(monkeypatch, capsys):
    out = run_with_inputs(monkeypatch, capsys, ["2", "1", "", "0", "0"])
    assert "TEACHER MENU" in out and "Goodbye" in out
