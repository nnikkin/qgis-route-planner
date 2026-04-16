from typing import Protocol


class ProfileProvider(Protocol):
    def get_profiles(self):
        pass

    def get_profile_by_id(self, current_profile_id):
        pass

    def create_profile(self, name, type, height_m, width_m, depth_m, weight_t):
        pass

    def update_profile(self, current_profile_id, profile):
        pass

    def delete_profile(self, profile_id):
        pass