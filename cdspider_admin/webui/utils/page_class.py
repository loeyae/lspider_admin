# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2019/6/20 17:01
"""

import math
class PageClass(object):
    def page_list(self, current_page, data_count, hits = 10):
        content = {}
        content['current_page'] = current_page
        content['offset'] = (current_page - 1) * hits
        content['count'] = data_count
        num_pages = math.ceil(int(data_count) / hits)
        content['num_pages'] = num_pages
        content['last_page'] = num_pages
        has_previous = True
        if current_page == 1:
            has_previous = False
        content['has_previous'] = has_previous
        has_next = True
        if current_page == num_pages or num_pages == 0:
            has_next = False
        content['has_next'] = has_next
        previous_page_number = current_page - 1
        content['previous_page_number'] = previous_page_number
        next_page_number = current_page + 1
        content['next_page_number'] = next_page_number
        return content

page_obj=PageClass()
