from collections import deque

TASK_ID_KEY = 'jobID'
TASK_STATUS_KEY = 'jobStatus'
TOTAL_PAGES_KEY = 'totalPage'
PAGE_NUMBER_KEY = 'pageNumber'
DATA_KEY = 'data'
DEFAULT_QUERY = ''
DEFAULT_QUERY_NAME = ''

class FetchingIterator:
    def __init__(self, 
                object_class,
                query, 
                params, 
                prefetched_page_json = None, 
                total_pages = None):
        self.queue = deque()
        self.object_class = object_class
        self.query = query
        self.params = params
        self.iteration_ended = False
        self.page_number = 0
        self.total_pages = 0

        self.__fetch_next_page(prefetched_page_json, total_pages)


    def __len__(self):
        return len(self._queue)

    def __iter__(self):
        return self

    def __next__(self):
        if not self._queue and not self._fetch_next_page():
            raise StopIteration()

        return self.queue.popleft()

    def __instatiate_typed_entities(self, json_entities):
        entities = []
        for json_entity in json_entities:
            entities.append(self.object_class(json_entity))
        return entities
    
    def __parse_response(self, response):
        total_pages = response.get(TOTAL_PAGES_KEY, 0)
        page_number = response.get(PAGE_NUMBER_KEY, 0)
        json_entities = response.get(DATA_KEY, {})
        return json_entities, page_number, total_pages
    
    def __fetch_next_page(self, prefetched_page, total_pages):
        if self.iteration_ended:
            return False
        
        if not prefetched_page:
            page_response = self.session.execute(self.query, self.params)
            json_entities, self.page_number, self.total_pages = self.__parse_response(page_response)
        else:
            json_entities, self.page_number, self.total_pages = self.__parse_response(prefetched_page)
       
        entities = self.__instatiate_typed_entities(json_entities)
        self.queue.append(entities)
        
        if self.page_number == total_pages:
            self.iteration_ended = True

        return True