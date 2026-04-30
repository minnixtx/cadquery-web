import os
import tempfile
import base64
import cadquery as cq


class ModelExporter:
    """Export CADQuery results to TJS, STL, or STEP format."""

    @staticmethod
    def _export(result, ext: str) -> bytes:
        """Write to a temp file and read back the bytes."""
        fd, tmp_path = tempfile.mkstemp(suffix=f".{ext}")
        try:
            os.close(fd)
            ext_upper = ext.upper()
            if ext_upper in cq.exporters.ExportTypes.__dict__.values():
                cq.exporters.export(result, tmp_path, exportType=ext_upper)
            else:
                cq.exporters.export(result, tmp_path)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @staticmethod
    def to_tjs(result) -> bytes:
        """Export to TJS (Three.js JSON) format, returns raw bytes."""
        return ModelExporter._export(result, "tjs")

    @staticmethod
    def to_tjs_base64(result) -> str:
        """Export to TJS format, returns base64-encoded string."""
        return base64.b64encode(ModelExporter.to_tjs(result)).decode("utf-8")

    @staticmethod
    def to_stl(result) -> bytes:
        """Export to STL format, returns raw bytes."""
        return ModelExporter._export(result, "stl")

    @staticmethod
    def to_step(result) -> bytes:
        """Export to STEP format, returns raw bytes."""
        return ModelExporter._export(result, "step")
