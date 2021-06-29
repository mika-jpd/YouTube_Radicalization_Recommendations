from Video import video

class YTQueue:
    def __init__(self, size=None, url=None):
        self.head = Node(video(url=url), url=url)
        self.max_size = size

    # takes in array of url and appends to the end of the queue
    def add_end(self, array):
        last = self.head
        while (last.next != None):
            last = last.next

        for i in range(0, len(array)):
            new = Node(video(url=array[i]), url=array[i])
            last.next = new
            last = new

            if(i == (len(array))):
                new.next = None

    #takes in a url, creates a node and sets it to head
    def enqueue(self, url):
        node = Node(video(url=url), url)
        node.next = self.head
        self.head = node

    def dequeue(self):
        old = self.head
        self.head = old.next

        return old

    def print_queue(self):
        last = self.head
        while (last.next != None):
            print(last.video.url)
            last = last.next

    def isEmpty(self):
        if(self.head == None):
            return True
        else:
            return False

class Node:
    def __init__(self, video, url):
        self.url = url
        self.video = video
        self.next = None