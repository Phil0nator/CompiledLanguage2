from globals import *
from Classes.Error import *
from Classes.Token import *
from Classes.DType import *


#############################
# optloadRegs is used to load
#   two values into registers,
#   unless they already exist in registers.
#   This function ensures that values are
#   loaded as few times as possible.
############################
def optloadRegs(a, b, op, o):
    instr=""
    o = a.type.copy()
    needLoadA = True
    needLoadB = True
    if(a.isRegister()):
        areg = a.accessor
        needLoadA=False
    else:
        areg = ralloc(a.type.isflt())
    
    if(b.isRegister()):
        breg = b.accessor
        needLoadB = False
    else:
        breg = ralloc(a.type.isflt())


    if(needLoadB): instr+=loadToReg(breg, b.accessor)
    if(needLoadA): instr+=loadToReg(areg, a.accessor)
    return areg, breg, o, instr



###########################
#   bringdown_memloc takes an expression component
#       and returns the instructions necessary
#       to reduce its pointer depth by one.
#       (used for member access and arrays)
############################
def bringdown_memloc( a):
    instr=""
    if(a.memory_location):
        instr+=f"mov {setSize( a.accessor, a.type.csize())}, {psizeoft(a.type)}[{a.accessor}]\n"
        instr+=maskset(a.accessor,a.type.csize())
        a.memory_location=False
    return instr

# do two bringdown_memloc calls in one
def bringdown_memlocs( a, b):
    return bringdown_memloc(a) + bringdown_memloc(b)



class ExpressionEvaluator:
    def __init__(self, fn):
        self.fn = fn


    def evaluatePostfix(self, pfix, evaluator):                  # evaluate a generated postfix list of EC's
        instr = ""
        stack = []      # used for evaluation
        o = VOID.copy()
        for e in pfix:  # for each component
            if(e.isoperation): 
                if(not operatorISO(e.accessor)): # if the operator takes two operands
                    b = stack.pop()              # second operand
                    if(len(stack) < 1): throw(HangingOperator(pfix[-1].token))

                    a = stack.pop()              # first operand
                    op = e.accessor              # 
                    
                    if(a.isconstint() and b.isconstint()): # optimize for constant expressions
                        stack.append(calculateConstant(a,b,op))
                    
                    # if one operand is constant
                    elif(b.isconstint() and not a.isconstint() and not a.type.isflt()): # optimize for semi constexpr
                        newinstr = None
                        
                        # if one arg is 0, and can be optimized, add no extra code.
                        if(b.accessor == 0 and op not in  ["/", "["] and op not in signed_comparisons):
                            apendee = a
                            newinstr = ""
                            newt = a.type.copy()

                        # if can be optimized through bitshift multiplication/division
                        if(op == "*" or op == "/"):

                            if(canShiftmul(b.accessor)):
                                newinstr = ""
                                newinstr+=bringdown_memloc(a)
                                if(a.isRegister()):
                                    areg = a.accessor
                                else:
                                    areg = ralloc(False)
                                    newinstr+=loadToReg(areg,a.accessor)
                                    
                                
                                if(op == "*"):
                                    newinstr+=f"shl {valueOf(areg)}, {shiftmul(b.accessor)}\n"
                                else:
                                    newinstr+=f"shr {valueOf(areg)}, {shiftmul(b.accessor)}\n"
                                a.accessor = areg
                                apendee = a
                            newt = a.type.copy()
                        
                        if(op in [">>", "<<"]):

                            newinstr = ""
                            newinstr+=bringdown_memloc(a)
                            if(a.isRegister()):
                                areg = a.accessor
                            else:
                                areg = ralloc(False)
                                newinstr+=loadToReg(areg,a.accessor)
                                
                            newinstr+=shiftInt(areg,b.accessor,op,a.type.signed)
                            a.accessor = areg
                            apendee = a
                            newt = a.type.copy()


                        # if no valid optimizations couild be made:
                        #       do the normal evaluation
                        if(newinstr == None): newinstr, newt, apendee = evaluator.performCastAndOperation(a,b,op,o)
                        
                        # push result
                        stack.append(apendee)
                        instr+=newinstr
                        o = newt.copy()




                    else: # no optimizations can be made:

                        # op is -> or .
                        if(op == T_PTRACCESS or op == T_DOT):

                            ninster, o, apendee = evaluator.memberAccess(a,b)
                            instr+=ninster
                            stack.append(apendee)



                        # op is any other op
                        else:
                            newinstr, newt, apendee = evaluator.performCastAndOperation(a,b,op,o)
                            stack.append(apendee)
                            instr+=newinstr
                            o = newt.copy()
                else: # op takes only one operand 


                    if(len(stack) < 1): throw(HangingOperator(pfix[-1].token))
                    a = stack.pop() # operand
                    

                    # op == !
                    if(e.accessor == T_NOT):
                        
                        ninstr, o, apendee = evaluator.evalNot(a)
                        stack.append(apendee)
                        instr+=ninstr

                    # op == ~
                    elif(e.accessor == T_ANOT):
                        
                        ninster, o, apendee = evaluator.evalANOT(a)
                        stack.append(apendee)
                        instr+=ninster


                    # op == &
                    elif(e.accessor == T_REFRIZE):
                        

                        ninster, o, apendee = evaluator.refrize(a)
                        stack.append(apendee)
                        instr+=ninster

                    # op == @    
                    elif(e.accessor == T_DEREF):

                        ninster, o, apendee = evaluator.derefrence(a)
                        stack.append(apendee)
                        instr+=ninster

                    # op == $<type>
                    elif(e.accessor == T_TYPECAST):

                        ninster, o, apendee = evaluator.typecast(a,e,o)
                        stack.append(apendee)
                        instr+=ninster

                    else:
                        print(e)
                        exit(1)


            else: # if element is not operator, push to stack
                stack.append(e)
        
        if(len(stack) != 1): 
            throw(HangingOperator(self.fn.current_token))
        final = stack.pop() # result

        # at this point the result must be properly casted/moved into the specified destination


        o = final.type.copy()
        
        return instr, final

















############################################
#
#   The RightSideEvaluator is used to evaluate expressions
#       for a final value (as opposed to an address).
#
#   For example:
#       int a = 210 / x + y;
#               ~~~~~~~~~~~
#
#   The underlined region would be passed into the RightSideEvaluator
#       as a postfix of Expression Components:
#
#   [ 210, x, /, y, + ]
#
###############################################
class RightSideEvaluator(ExpressionEvaluator):
    def __init__(self, fn):
        self.fn = fn


    def evalNot(self, a):
        # must be bool compatible
        instr = ""
        if(not typematch(BOOL, a.type) and not a.isconstint()):
            throw(TypeMismatch(a.token,BOOL, a.type))
        
        # bring down memory location
        instr+=bringdown_memloc(a)
        
        # load to register if necessary
        needload = True
        if(a.isRegister()):
            areg = a.accessor
            needload=False
        else:
            areg = ralloc(False)
        if(needload): instr+=loadToReg(areg,a.accessor)

        # do not
        instr+=boolmath(areg,None,T_NOT)
        o = BOOL.copy()
        return instr, o, EC.ExpressionComponent(areg,BOOL.copy(),token=a.token)





    def evalANOT(self, a):
        needload=True
        instr = ""
        instr+=bringdown_memloc(a)
        if(a.isRegister()):
            areg = a.accessor
            needload=False
        else:
            areg = ralloc(False)
        if(needload): instr+=loadToReg(areg,a.accessor)
        instr+=doOperation(a.type,areg,areg,T_ANOT,a.type.signed)
        o = a.type.copy()
        return instr, o, EC.ExpressionComponent(areg,o.copy(),token=a.token)





    def refrize(self, a):
        instr = ""
        if( a.isconstint() ):
                            
            throw(AddressOfConstant(a.token))

        elif( isinstance(a.accessor, Variable) ):
            
            result = ralloc(False)
            if(a.accessor.isStackarr):
                instr+=f"lea {result}, [rbp-{a.accessor.offset+a.accessor.stackarrsize}]\n"
            else:

                instr+=f"lea {result}, [rbp-{a.accessor.offset}]\n"
            o = a.type.copy()
            o.ptrdepth+=1
            return instr, o, EC.ExpressionComponent(result, o.copy(),token=a.token)
        
        elif(a.memory_location):
            a.memory_location = False
            o = a.type.copy()
            o.ptrdepth+=1
            return instr, o, EC.ExpressionComponent(a.accessor, o.copy(),token=a.token)

        else:
            throw(AddressOfConstant(a.token))





    def derefrence(self, a):
        instr = ""
        if( a.isconstint() ):

            throw(AddressOfConstant(a.token))

        elif(isinstance(a.accessor, Variable)):

            tmp = ralloc(False)
            instr+=f"mov {tmp}, {valueOf(a.accessor)}\n" 
            if(a.accessor.t.isflt()):
                oreg = ralloc(True)
                instr+=f"movsd {oreg}, [{tmp}]\n"
            else:
                oreg = ralloc(False)
                instr+=maskset(oreg,a.type.size(1))
                instr+=f"mov {setSize( oreg, a.type.size(1))}, {psizeoft(a.type, 1)}[{tmp}]\n"
            o = a.accessor.t.copy()
            o.ptrdepth-=1
            rfree(tmp)
            return instr, o, EC.ExpressionComponent(oreg, o.copy(),token=a.token)
        elif(a.isRegister()):
            result = ralloc(a.type.isflt())
            if(a.type.isflt()):
                instr+=f"movsd {result}, [{a.accessor}]\n"
            else:
                instr+=f"mov {result}, [{a.accessor}]\n"
            rfree(a.accessor)
            o = a.type.copy()
            o.ptrdepth-=1
            return instr, o, EC.ExpressionComponent(result, o.copy(),token=a.token)



    def typecast(self, a, e, o):
        instr = ""
        tid = e.type
        t = self.fn.compiler.getType(tid)
        if(t == None):
            throw(UnkownType(e.token))
        aval = ralloc(a.type.isflt())
        result = ralloc(t.isflt())
        instr+=bringdown_memloc(a)
        cst=castABD(EC.ExpressionComponent("",t),EC.ExpressionComponent("",a.type),"",aval,result)
        if(cst != False):
            instr+=loadToReg(aval, a.accessor)
            instr+=cst
            rfree(aval)
            return instr, o , EC.ExpressionComponent(result,t.copy(),token=a.token)
        else:
            rfree(aval)
            rfree(result)
            return instr, o, EC.ExpressionComponent(a.accessor,t.copy(),token=a.token)



    # (used for rightside evaluation)
    def performCastAndOperation(self,a, b, op, o):                      # Do an operation with a op b -> o:DType
        instr = ""
        apendee = None
        if(op in ["<<", ">>"]):
            if( (a.type.isflt() or b.type.isflt())):
                throw(InvalidOperationOperands(a.token,op,a.type,b.type))
            


        instr+=bringdown_memlocs(a,b)

        if(op == "["):
            if(b.type.isflt()): throw(UsingFloatAsIndex(b.token))
            
            
            areg, breg, o, ninstr = optloadRegs(a,b,op,o)
            instr+=ninstr
            if(a.type.size(1) in [1,2,4,8]):
                instr+=f"lea {areg}, [{areg}+{breg}*{a.type.size(1)}]\n"
            else:
                if(canShiftmul(a.type.size(1))):
                    instr+=f"shl {breg}, {shiftmul(a.type.size(1))}\n"
                else:
                    instr+=f"imul {breg}, {a.type.size(1)}\n"
                instr+=f"lea {areg}, [{areg}+{breg}]\n"
            apendee = (EC.ExpressionComponent(areg, a.type.down(),token=a.token))
            apendee.memory_location = True
            rfree(breg)

        

        elif(a.type.__eq__(b.type)):
            #same type

            areg, breg, o, ninstr = optloadRegs(a,b,op,o)
            instr+=ninstr
            instr+=doOperation(a.type,areg, breg, op, a.type.signed or b.type.signed)
            if(op in ["==","!=",">","<","<=",">="]):
                if(a.type.isflt() or b.type.isflt()):
                    rfree(areg)
                    areg = f"{rax}"
                a.type = BOOL.copy()

            apendee = (EC.ExpressionComponent(areg,a.type,token=a.token))

            rfree(breg)
        else: #situation is different when casting is directional
            if(not typematch(a.type,b.type) and not typematch(b.type, a.type) and not (a.isconstint() or b.isconstint())):
                throw(TypeMismatch(a.token, a.type, b.type))
            newtype, toConvert = determinePrecedence(a.type, b.type,self.fn)
            o = newtype.copy()
            if(newtype.__eq__(a.type)):
                # cast to a
                castee = b
                caster = a
            else:
                #cast to b
                castee = a
                caster = b
            
            needLoadC = True
            needLoadCO = True

            if(caster.isRegister()):
                creg = caster.accessor
                needLoadC=False
            else:
                creg = ralloc(caster.type.isflt())
            
            if(castee.isRegister()):
                coreg = castee.accessor
                needLoadCO = False
            else:
                coreg = ralloc(castee.type.isflt())

            newcoreg = ralloc(caster.type.isflt())
            
            if(needLoadC): instr+=loadToReg(creg, caster.accessor)
            if(needLoadCO): instr+=loadToReg(coreg, castee.accessor)
            cst=castABD(caster,castee,creg,coreg,newcoreg)
            #cst represents if actual extra instructions are needed to cast
            if(cst!=False):
                instr+=cst
            else:
                rfree(newcoreg)
                newcoreg = coreg


            instr+=doOperation(caster.type,creg,newcoreg,op, caster.type.signed)
            # handle float comparison
            if(op in ["==","!=",">","<","<=",">="]):

                if( caster.type.isflt() or castee.type.isflt()):                    
                    rfree(creg)
                    creg = f"{rax}"
                caster.type = BOOL.copy()
                o = BOOL.copy()


            apendee = (EC.ExpressionComponent(creg,caster.type,token=caster.token))
            rfree(newcoreg)
            rfree(coreg)


        
        return instr, o, apendee

    def memberAccess(self, a, b):
        instr = ""
        member = b.accessor
        memv = a.type.getMember(member)
        if(memv == None): throw(UnkownIdentifier(b.token))
        o = memv.t.copy()


        tmpaddr = ralloc(False)
        #instr+=f"mov {tmpaddr}, {valueOf(a.accessor)}\n"
        instr+=loadToReg(tmpaddr, a.accessor)

        
        
        rfree(a.accessor)
        
        
        
        
        instr+=f"lea {tmpaddr}, [{tmpaddr}+{memv.offset}]\n"
        apendee = EC.ExpressionComponent(tmpaddr, memv.t.copy(),token=b.token)
        apendee.memory_location=True
        return instr, o, apendee



    def depositFinal(self, final, o, dest):
        instr = ""
        instr+=bringdown_memloc(final)
        if(dest == "AMB"):
            if(final.isRegister()):
                rfree(final.accessor)
            return instr, o

        if(final.type.__eq__(dest.type)):

            if(isinstance(final.accessor, Variable)):
                tmp = ralloc(final.type.isflt())
                instr+=loadToReg(tmp, final.accessor)

                final.accessor = tmp
                rfree(tmp)
            else:
                rfree(final.accessor)
            instr+=loadToReg(dest.accessor,final.accessor)



        else:

            #not needed error
            #if(not typematch(dest.type, final.type)):
            #throw(TypeMismatch(dest.token, dest.type, final.type))



            twoStep = False
            if(isinstance(dest.accessor, Variable)):
                castdest = ralloc(dest.type.isflt())
                twoStep = True
            else:
                castdest = dest.accessor

            if(dest.type.isflt() and not final.type.isflt()):
                if(isinstance(final.accessor, int)):
                    instr+=f"mov {rax}, {final.accessor}\n"
                    final.accessor = "rax"
                elif(final.accessor == "pop"):
                    instr+=f"pop {rax}\n"
                    final.accessor = "rax"

                cst = f"cvtsi2sd {valueOf(castdest)}, {valueOf(final.accessor)}\n"
            elif(not dest.type.isflt() and final.type.isflt()):
                if(final.accessor == "pop"):
                    instr+=f"pop {rax}\nmovq {xmm7}, {rax}\n"
                    final.accessor = "xmm7"

                cst = f"cvttsd2si {valueOf(castdest)}, {valueOf(final.accessor)}\n"
            else:
                cst = False
            
            
            if(cst!=False):
                instr+=cst
                if(twoStep):
                    instr+=loadToReg(dest.accessor, castdest)

            else:
                source = final.accessor
                if(isinstance(final.accessor, Variable)):
                    instr+=loadToReg(castdest, final.accessor)
                    source = castdest
                instr+=loadToReg(dest.accessor,source)

            if(final.isRegister()):
                rfree(final.accessor)

            rfree(castdest)


        return instr, o




    def evaluate(self, dest, pfix):
        instr, final = self.evaluatePostfix(pfix,self)
        ninster, o = self.depositFinal(final,final.type,dest)
        return instr+ninster,o

    


############################################
#
#   The LeftSideEvaluator is used to evaluate expressions
#       for a destination address.
#
#   For example:
#       array[0]->chars[36] = 'a';
#       ~~~~~~~~~~~~~~~~~~~
#
#   The underlined region would be passed into the LeftSideEvaluator
#       as a postfix of Expression Components:
#
#   [ array, 0, [, chars, 36, [, -> ]
#
###############################################
class LeftSideEvaluator(ExpressionEvaluator):
    def __init__(self, fn):
        self.fn = fn
    



    def performCastAndOperation(self,a, b, op, o):                      # Do an operation with a op b -> o:DType
        instr = ""
        apendee = None

        if(op == "["):
            if(b.type.isflt()): throw(UsingFloatAsIndex(b.token))
            
            instr+=bringdown_memlocs(a,b)
            
            if(b.isconstint() and b.accessor == 0): # index 0 means nothing
                return "", a.type.copy(), a



            areg, breg, o, ninstr = optloadRegs(a,b,op,o)
            instr+=ninstr
                

            if(a.type.size(1) in [1,2,4,8]):
                instr+=f"lea {areg}, [{areg}+{breg}*{a.type.size(1)}]\n"
            else:
                if(canShiftmul(a.type.size(1))):
                    instr+=f"shl {breg}, {shiftmul(a.type.size(1))}\n"
                else:
                    instr+=f"imul {breg}, {a.type.size(1)}\n"
                instr+=f"lea {areg}, [{areg}+{breg}]\n"
            apendee = (EC.ExpressionComponent(areg, a.type.down(),token=a.token))
            apendee.memory_location = True
            rfree(breg)
            
            return instr, o, apendee

        

        rev = RightSideEvaluator(self.fn)
        return rev.performCastAndOperation(a,b,op,o)

    def memberAccess(self, a,b):
        instr = ""
        member = b.accessor
        memv = a.type.getMember(member)
        if(memv == None): throw(UnkownIdentifier(b.token))
        o = memv.t.copy()


        tmpaddr = ralloc(False)
        #instr+=f"mov {tmpaddr}, {valueOf(a.accessor)}\n"
        instr+=loadToReg(tmpaddr, a.accessor)

        if(memv.offset != 0):
            instr+=f"lea {tmpaddr}, [{tmpaddr}+{memv.offset}]\n"

        rfree(a.accessor)
        return instr, o, EC.ExpressionComponent(tmpaddr,memv.t.copy(),token=b.token)


    def evalNot(self, a):
        instr = ""
        if(not typematch(BOOL, a.type) and not a.isconstint()):
            throw(TypeMismatch(a.token,BOOL, a.type))
        
        needload = True
        if(a.isRegister()):
            areg = a.accessor
            needload=False
        else:
            areg = ralloc(False)
        if(needload): instr+=loadToReg(areg,a.accessor)

        instr+=boolmath(areg,None,T_NOT)
        o = BOOL.copy()
        return instr, o, EC.ExpressionComponent(areg,BOOL.copy(),token=a.token)


    def evalANOT(self, a):
        instr = ""
        needload=True
        if(a.isRegister()):
            areg = a.accessor
            needload=False
        else:
            areg = ralloc(False)
        if(needload): instr+=loadToReg(areg,a.accessor)
        instr+=doOperation(a.type,areg,areg,T_ANOT,a.type.signed)
        o = a.type.copy()
        return instr, o, EC.ExpressionComponent(areg,o.copy(),token=a.token)

    def refrize(self, a):
        instr = ""
        if( a.isconstint() ):

            throw(AddressOfConstant(a.token))

        elif( isinstance(a.accessor, Variable) ):
            
            result = ralloc(False)
            if(a.accessor.isStackarr):
                instr+=f"lea {result}, [rbp-{a.accessor.offset+a.accessor.stackarrsize}]\n"
            else:

                instr+=f"lea {result}, [rbp-{a.accessor.offset}]\n"
            o = a.type.copy()
            o.ptrdepth+=1
            return instr, o, EC.ExpressionComponent(result, o.copy(),token=a.token)
        

        else:
            throw(AddressOfConstant(a.token))


    def derefrence(self, a):
        instr = ""
        if( a.isconstint() ):

            throw(AddressOfConstant(a.token))

        elif(isinstance(a.accessor, Variable)):

            tmp = ralloc(False)
            instr+=f"mov {tmp}, {valueOf(a.accessor)}\n" 
            if(a.accessor.t.isflt()):
                oreg = ralloc(True)
                instr+=f"movsd {oreg}, {tmp}\n"
            else:
                oreg = ralloc(False)
                instr+=f"mov {oreg}, {tmp}\n"
            o = a.accessor.t.copy()
            o.ptrdepth-=1
            rfree(tmp)
            return instr, o , EC.ExpressionComponent(oreg, o.copy(),token=a.token)


        elif(a.isRegister()):
            result = ralloc(a.type.isflt())
            if(a.type.isflt()):
                instr+=f"movsd {result}, {a.accessor}\n"
            else:
                instr+=f"mov {result}, {a.accessor}\n"
            rfree(a.accessor)
            o = a.type.copy()
            o.ptrdepth-=1
            return instr, o, EC.ExpressionComponent(result, o.copy(),token=a.token)

    def typecast(self, a, e, o):
        instr = ""
        tid = e.type
        t = self.fn.compiler.getType(tid)
        if(t == None):
            throw(UnkownType(e.token))
        aval = ralloc(a.type.isflt())
        result = ralloc(t.isflt())
        cst=castABD(EC.ExpressionComponent("",t),EC.ExpressionComponent("",a.type),"",aval,result)
        if(cst != False):
            instr+=loadToReg(aval, a.accessor)
            instr+=cst
            rfree(aval)
            appendee = EC.ExpressionComponent(result,t.copy(),token=a.token)
        else:
            rfree(aval)
            rfree(result)
            appendee = EC.ExpressionComponent(a.accessor,t.copy(),token=a.token)
        return instr, o, appendee

    def depositFinal(self, final, o, dest):
        return "", final.type


    def evaluate(self, pfix):
        return self.evaluatePostfix(pfix, self)