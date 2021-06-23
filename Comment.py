import anytree
class comment:
    def __init__(self, user, date, text, user_url, parent=None):
        self.text = text
        self.parent = parent
        self.user = user
        self.user_url = user_url
        self.date = self.absolute_date(date)

    #given a relative date, sets the absolute date to the object field
    def absolute_date(self, date):
        pass

    #returns the user id from url
    def url_to_id(self, url):
        pass