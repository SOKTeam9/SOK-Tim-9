from django.apps import AppConfig
import os
from webapp.views import filters, current_view, apply_filter


class WebappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webapp'

    def load_session():
        global current_view
        filters.clear()
        with open("session.txt", "r") as f:
            filter_string = f.readline().strip()
            list_filters = filter_string.split(",")

            for single_filter in list_filters:
                single_parts_list = single_filter.split("~")
                print(single_parts_list)
                if single_parts_list[0] != "":
                    filters.append((single_parts_list[0], single_parts_list[1], single_parts_list[2]))
            
            current_view = f.readline().strip()
        
        apply_filter()

    def ready(self):
        if os.path.exists("session.txt") and os.path.getsize("session.txt") != 0:
            self.load_session()
            print("AAAASDASDS")