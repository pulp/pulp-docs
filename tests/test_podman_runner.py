from pathlib import Path

from pulp_docs.openapi import PodmanContainer


class TestPodmanContainer:
    def test_dry_run_lifecycle(self, tmp_path, capsys):
        """Test dry run mode prints all commands."""
        c = PodmanContainer(
            image="myimage",
            volumes={str(tmp_path): "/output"},
            env={"FOO": "BAR"},
            dry_run=True,
        )
        with c.run():
            c.exec("echo", "hello")

        output = capsys.readouterr().out
        assert "podman create" in output
        assert "podman start" in output
        assert "podman exec" in output
        assert "echo hello" in output
        assert "podman rm --force" in output
        assert "FOO=BAR" in output
        assert f"{tmp_path}:/output:Z" in output

    def test_volume_mount_write(self, tmp_path: Path):
        """Test that files written inside container are accessible on host."""
        container = PodmanContainer(
            image="quay.io/pulp/pulp-minimal:stable",
            volumes={str(tmp_path): "/output"},
        )

        with container.run():
            container.exec("bash", "-c", "echo 'test content' > /output/test.txt")

        test_file = tmp_path / "test.txt"
        assert test_file.exists()
        assert test_file.read_text() == "test content\n"
