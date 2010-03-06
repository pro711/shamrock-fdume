import copy

try:
    from ragendja.dbutils import prefetch_references
except ImportError:
    prefetch_references = None


class Paginator(object):
    def __init__(self, object_query, order_by, per_page=10, prefetch=None):
        self.object_query = object_query
        self.order_by = order_by
        # Are we ascending?
        if order_by[0] != '-':
            self.reverse_order_by = '-%s' % order_by
            self.compare = '>='
            self.reverse_compare = '<'
            self.property = order_by
        else:   # Descending
            self.reverse_order_by = '%s' % order_by[1:]
            self.compare = '<='
            self.reverse_compare = '>'
            self.property = order_by[1:]
        self.per_page = per_page
        self.prefetch = prefetch
    
    def _page_values(self, start_value):
        object_list = []
        previous_entity = None
        next_entity = None
        previous_object_list = None
        if self.object_query is not None:
            object_query_copy = copy.deepcopy(self.object_query)
            if start_value is None:
                object_list = object_query_copy.order(self.order_by).fetch(
                    self.per_page + 1
                )
            else:
                object_list = object_query_copy.filter(
                    '%s %s' % (self.property, self.compare),
                    start_value
                ).order(self.order_by).fetch(self.per_page + 1)
                object_query_copy2 = copy.deepcopy(self.object_query)
                previous_object_list = object_query_copy2.filter(
                    '%s %s' % (self.property, self.reverse_compare),
                    start_value
                ).order(self.reverse_order_by).fetch(self.per_page)
                if len(previous_object_list) > 0:
                    previous_entity = previous_object_list[-1]
            if len(object_list) > self.per_page:
                next_entity = object_list[-1]
                object_list = object_list[:self.per_page]
            if self.prefetch and prefetch_references is not None:
                object_list = prefetch_references(object_list, self.prefetch)
        return object_list, previous_entity, next_entity
    
    def page(self, start_value):
        object_list, previous_entity, next_entity = self._page_values(
            start_value
        )
        next_page_value = None
        previous_page_value = None
        if previous_entity:
            previous_page_value = getattr(
                previous_entity, self.property, None
            )
        if next_entity:
            next_page_value = getattr(
                next_entity, self.property, None
            )
        return Page(
            object_list, start_value, self,
            next_page_value=next_page_value,
            previous_page_value=previous_page_value
        )
    


class Page(object):
    def __init__(
            self, object_list, start_value, paginator,
            next_page_value=None, previous_page_value=None
        ):
        self.object_list = object_list
        self.start_value = start_value
        self.paginator = paginator
        self.next_page_value = next_page_value
        self.previous_page_value = previous_page_value
    
    def has_next(self):
        return self.next_page_value is not None
    
    def has_previous(self):
        return self.previous_page_value is not None
    
    def has_other_pages(self):
        return self.has_next() or self.has_previous()
    

