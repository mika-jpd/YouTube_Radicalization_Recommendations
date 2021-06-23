class node:
    def __init__(self, video, children):
        self.video = video
        self.children = children

    def addChildren(self, children):
        self.children = children

    def addVideo(self, video):
        self.video = video