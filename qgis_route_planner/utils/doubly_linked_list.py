class DLLNode:
    def __init__(self, value):
        self.value = value
        self.next = None
        self.prev = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self._length = 0

    def __len__(self):
        return self._length

    def __iter__(self):
        current = self.head
        while current:
            yield current.value
            current = current.next

    def append(self, value):
        new_node = DLLNode(value)
        if not self.head:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self._length += 1

    def clear(self):
        self.head = self.tail = None
        self._length = 0

    def remove_by_id(self, value_id: int):
        current = self.head
        while current:
            if current.value.id == value_id:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next

                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev

                self._length -= 1
                return current.value
            current = current.next
        return None

    def traverse(self, reverse_traverse: bool = False):
        current = self.head if reverse_traverse else self.tail
        while current:
            print(current.data, end=" <-> ")
            current = current.next if reverse_traverse else current.prev
        print("None")

    def find(self, value):
        current = self.head
        while current:
            if current.data == value:
                return current
            current = current.next
        return None

    def sort_by_order(self):
        """Простая сортировка вставками"""
        if not self.head or not self.head.next:
            return

        values = list(self)
        values.sort(key=lambda p: p.order)

        self.clear()
        for v in values:
            self.append(v)
