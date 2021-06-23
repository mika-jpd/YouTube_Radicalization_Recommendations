import anytree
class Node:
    def __init__(self, dataval=None):
        self.dataval = dataval
        self.nextval = None

class SLinkedList:
    def __init__(self):
        self.headval = None

    def listprint(self):
        printval = self.headval
        while printval is not None:
            print(printval.dataval)
            printval = printval.nextval

        def insert_begining(self, newdata):
            NewNode = Node(newdata)
            # Update the new nodes next val to existing node
            NewNode.nextval = self.headval
            self.headval = NewNode

        def insert_end(self, newdata):
            NewNode = Node(newdata)
            if self.headval is None:
                self.headval = NewNode
                return
            laste = self.headval
            while (laste.nextval):
                laste = laste.nextval
            laste.nextval = NewNode

        def insert_inbetween(self, middle_node, newdata):
            if middle_node is None:
                print("The mentioned node is absent")
                return

            NewNode = Node(newdata)
            NewNode.nextval = middle_node.nextval
            middle_node.nextval = NewNode

        def RemoveNode(self, Removekey):
            HeadVal = self.headval
            if (HeadVal is not None):
                if (HeadVal.dataval == Removekey):
                    self.headval = HeadVal.next
                    HeadVal = None
                    return

            while (HeadVal is not None):
                if HeadVal.data == Removekey:
                    break
                prev = HeadVal
                HeadVal = HeadVal.next

            if (HeadVal == None):
                return

            prev.next = HeadVal.next
            HeadVal = None