#
#   Load
#   PreTokenize
#   PreProcess
#   Tokenize
#   Compile
#   Optimize
#   Link
#   
#
import time
import os
import argparse as arg
from Error import *
from globals import *

from Variable import *
from Function import *
from DType import *
from Token import *
from Location import *
from PreParser import *
from Compiler import *
from Linker import *

def main():
    beginTime = time.time()
    with open(__fileinput__, "rb") as inpf:
        raw = inpf.read().decode()

    pre = PreParser(raw,__fileinput__)
    pretokens = pre.getTokens() 

    pp = PreProcessor(raw,pretokens,__fileinput__)
    totals = pp.process()
    print("+-+-+ Compile +-+-+")
    c = Compiler()

    

    for file in totals:
        
        c.compile(file)

    c.finalize()

    asm = "%s"%fileTemplate
    asm = asm.replace("%%HEAP%%", c.heap)
    asm = asm.replace("%%CONSTANTS%%", c.constants)
    asm = asm.replace("%%TEXT%%", c.text)
    asm = asm.replace("%%INITIALIZE%%", c.initializers)
    asm = asm.replace("%%ENTRY%%", c.entry)
    

    #asm = asm.replace("\n\n","\n").replace("\n\n","\n").replace("\t","")
    
    print("+-+-+ FINAL +-+-+")
    
    with open(__fileoutput__+".asm", "wb") as f:
        f.write(asm.encode())

    os.system(assemble(__fileoutput__))
    os.system(link(__fileoutput__,__fileoutput__))
    os.remove(__fileoutput__+".o")

    if(not __tonasm__):
        os.remove(__fileoutput__+".asm")

    print("Compiled and Linked symbols in %s ms"%(time.time()-beginTime))
    if(__autorun__):
        os.system(f"./{__fileoutput__}")



parser = arg.ArgumentParser(description='Compile .rud programs into either nasm assembly, or to an executable.')
parser.add_argument("-o", "--output", required=True)
parser.add_argument("-i", "--input", required=True)
parser.add_argument("-nasm", action="store_true", default=False)
parser.add_argument("-r", action="store_true", default=False)
parser.add_argument("-g", action="store_true",default=False)
args = parser.parse_args()
__fileinput__=args.input
__fileoutput__=args.output
__tonasm__=args.nasm
__autorun__=args.r
__dbg__ = args.g


main()