from typing import Protocol


class ProfileProvider(Protocol):
    def get_profiles(self):
        pass

    def get_profile_by_id(self, current_profile_id):
        pass

    def create_profile(self, name: str, vtype, height: float, width: float, depth: float, weight: float):
        pass

    def update_profile(self, current_profile_id, profile):
        pass

    def delete_profile(self, profile_id):
        pass