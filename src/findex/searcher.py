from findex.indexer import InvertedIndex

class BooleanSearch:
    def __init__(self, index: InvertedIndex):
        self.index = index

    def search_and_merge(self, term1: str, term2: str) -> list[int]:
        """Двовказівниковий алгоритм для відсортованих списків (Merge)."""
        list1 = self.index.postings.get(term1, [])
        list2 = self.index.postings.get(term2, [])
        
        result = []
        i, j = 0, 0
        while i < len(list1) and j < len(list2):
            if list1[i].doc_id == list2[j].doc_id:
                result.append(list1[i].doc_id)
                i += 1
                j += 1
            elif list1[i].doc_id < list2[j].doc_id:
                i += 1
            else:
                j += 1
        return result

    def search_and_set(self, term1: str, term2: str) -> list[int]:
        """Альтернатива через вбудований Python set (зазвичай швидша через C-імплементацію)."""
        set1 = {p.doc_id for p in self.index.postings.get(term1, [])}
        set2 = {p.doc_id for p in self.index.postings.get(term2, [])}
        return sorted(list(set1 & set2))