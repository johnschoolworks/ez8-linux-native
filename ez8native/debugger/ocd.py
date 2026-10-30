"""No target operations are implemented or permitted in V0.1."""
from .safety import deny_target_operation


class Z8OCD:
    def read_id(self):
        deny_target_operation("read_id")

    def read_memory(self, *args, **kwargs):
        deny_target_operation("read_memory")

    def reset(self):
        deny_target_operation("reset")

    def flash_unlock(self):
        deny_target_operation("flash_unlock")

    def page_erase(self, *args, **kwargs):
        deny_target_operation("page_erase")

    def mass_erase(self):
        deny_target_operation("mass_erase")

    def program_flash(self, *args, **kwargs):
        deny_target_operation("program_flash")
