###################################
#
#   The Variable class is used to represent both global and local
#       variables of any type.
#   It sotores a variable's scope, name, stack offset, initializer, data type, and
#       some other usage hints.
#
#   \see Function
#   \see Compiler
#   \see DType
#
###################################
class Variable:
    def __init__(self, t, name, glob=False, offset=0, initializer=0,
                 isptr=False, mutable=True, signed=True, isStackarr=False):
        self.t = t                      # data type
        self.name = name                  # str: name
        self.glob = glob                  # bool: is global
        self.offset = offset              # ptr offset (stack or otherwise)
        self.initializer = initializer  # original value for globals
        self.isptr = isptr              # bool: is pointer value
        self.mutable = mutable          # bool: is constant or mutable
        # bool: is signed (redundant to DType.signed)
        self.signed = signed
        self.isStackarr = isStackarr    # bool: is stack based array
        self.stackarrsize = t.csize()   # if it's a stack based array, how big is it?
        # if it's a stack based array, what are the dimentions
        self.stackdims = isStackarr
        self.stacksizes = []            # ^ sizes
        self.register = None            # register declaration

    def isflt(self):  # redundant to DType.isflt
        # return (self.t.name == "float" or self.t.name == "double") and
        # self.isptr == False
        return self.t.isflt()

    def __repr__(self):  # pretty print
        if(self.isStackarr):
            return f"[{self.t} {self.name}[{self.stackarrsize}] @ {self.offset} -> {self.offset+self.stackarrsize}]]"
        else:
            return f"[{self.t} {self.name} @ {(self.offset)}]" if self.register is None else f"[{self.t} {self.name} @ {self.register}]"
