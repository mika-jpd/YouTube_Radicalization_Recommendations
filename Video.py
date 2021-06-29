import anytree
class video:
    def __init__(self, url, title=None, content_creator=None, description=None, date=None, views=None, comments=None, likes=None, dislikes=None, transcript=None, tags=None, video_length=None, ad=None, id=None):
        self.url = url
        self.title = title
        self.content_creator = content_creator
        self.description = description
        self.date = date
        self.views = views
        self.comments = comments #array of linked list of comments objects, must process
        self.likes = likes
        self.dislikes = dislikes
        self.transcript = transcript
        self.tags = tags
        self.video_length = video_length
        self.id = id
        self.ad = ad
        self.category = None
        self.dataset = None

    #takes in array of comments, outputs linkedList of comments where head is top comment and nextval is the next reply
    def comment_processing(self, comments):
        pass

    #parse dataset to get channel category
    def channel_category(self, df):
        pass