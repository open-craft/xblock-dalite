"""Test utilities."""
import mock


class TestWithPatchesMixin(object):
    """Test Mixin providing a bit easier-to-use patching interface."""

    def make_patch(self, obj, member_name, new=mock.DEFAULT):
        """Patch `member_name` in `obj` with `new` and restore after each test."""
        patcher = mock.patch.object(obj, member_name, new)
        patch_instance = patcher.start()
        self.addCleanup(patcher.stop)
        return patch_instance
