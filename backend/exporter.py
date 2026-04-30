import os
import tempfile
import base64


class ModelExporter:
    """Export CADQuery results to OBJ, STL, or STEP format."""

    @staticmethod
    def _export(result, ext: str) -> bytes:
        """Write to a temp file and read back the bytes."""
        fd, tmp_path = tempfile.mkstemp(suffix=f".{ext}")
        try:
            os.close(fd)
            result.export(tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @staticmethod
    def to_obj(result) -> bytes:
        """Export to OBJ format, returns raw bytes."""
        return ModelExporter._export(result, "obj")

    @staticmethod
    def to_obj_base64(result) -> str:
        """Export to OBJ format, returns base64-encoded string."""
        return base64.b64encode(ModelExporter.to_obj(result)).decode("utf-8")

    @staticmethod
    def to_stl(result) -> bytes:
        """Export to STL format, returns raw bytes."""
        return ModelExporter._export(result, "stl")

    @staticmethod
    def to_step(result) -> bytes:
        """Export to STEP format, returns raw bytes."""
        return ModelExporter._export(result, "step")
