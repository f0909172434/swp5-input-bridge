from swp5_input.cli import main


def test_plan_expression(capsys):
    code = main(["plan", "--expr", r"K_\rho=0"])
    assert code == 0
    output = capsys.readouterr().out
    assert "math_start" in output
    assert "subscript" in output
    assert "tex: 'rho'" in output
    assert "math_end" in output


def test_write_requires_yes(capsys):
    code = main(["write", "--expr", "x=1"])
    assert code == 2
    assert "--yes" in capsys.readouterr().err
