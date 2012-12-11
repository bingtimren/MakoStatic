#!/usr/bin/python

import sys, getopt, os
from mako.template import Template
from mako.lookup import TemplateLookup
from mako.runtime import UNDEFINED
from mako.exceptions import TopLevelLookupException
import mako.runtime
import shutil
import types
import imp
import inspect
import string
import pkgutil
from StringIO import StringIO
import traceback


TEMPLATE_DIR = "template"
OUTPUT_DIR = "output"
ROOT_CONTEXT = "msctx_root"
MODULE_ATTACH = "__msctx__"
PATHDEFAULT_TEMP = "path_default.html"
MS_USETEMP = "MS_USE_TEMPLATE"
PAGE_SUFFIX=".html"
TEMP_SUFFIX=".html"
NOT_RESOURCE_SUFFIX=["py","pyc",TEMP_SUFFIX[1:]]
MS_ROOT = "ms_root"
MS_SELF = "ms_self"
CTX_MUST_HAVE = "CTX_MUST_HAVE"



# try to load a ctx according to "a.b" like path, return ctx otherwise None
def tryMsContext(path):
    if path != "":
        name = string.join([ROOT_CONTEXT, path],".")
    else:
        name = ROOT_CONTEXT
    # print "test module ",name
    m = tryToImport(name)
    # print m
    return __wrap__(m)

def tryToImport(name, hasToSuccess=False):
    # print "tryToImport: ",name
    # have to say, stupid __import__ depends on fromlist
    if not hasToSuccess:
        try:
            m = __import__(name, fromlist=[name])
            assert m.__name__ == name
        except:
            m = None
    else:
        m = __import__(name, fromlist=[name])
    # print "tryToImport: ", m
    return m

# wrap a module as a MsContext otherwise return the same
def __wrap__(thing):
    if inspect.ismodule(thing):
        if MODULE_ATTACH in dir(thing):
            return getattr(thing, MODULE_ATTACH)
        else:
            return MsContext(thing)
    return thing

# get the value or a submodule from module, None maybe means not found

# the MakoStatic context, enclosing a module with added functions
class MsContext:
    ctx_module = None # must be a python module
    ctx_path = None
    ctx_name = None
    parent = None # must be a MsContext
    is_path_module = None
    is_root = None
    __children__ = None
    # a MsContext is a module, therefore needs a module to initiate
    def __init__(self, ctx_module):
        assert inspect.ismodule(ctx_module) , "ctx_module needs to be a module!"
        assert ctx_module.__name__.startswith(ROOT_CONTEXT), "ctx_module has to be under "+ROOT_CONTEXT+"!"
        self.ctx_module = ctx_module
        setattr(ctx_module,MODULE_ATTACH,self)
        self.is_root = ctx_module.__name__ == ROOT_CONTEXT
        mod_path = ctx_module.__name__.split('.')
        self.ctx_path = string.join(mod_path[1:],".")
        if len(mod_path) > 1:
            self.ctx_name = mod_path[-1]
        else:
            self.ctx_name = ""
        # is a module for a dir? (not a .py)
        is_path_module = '__path__' in dir(ctx_module) and (ctx_module.__file__.endswith('__init__.pyc') or ctx_module.__file__.endswith('__init__.py'))
        self.is_path_module = is_path_module
        parent_path = string.join(mod_path[:-1],'.') # "" if len(mod_path) == 1
        # try to get the parent module
        parent_mod = tryToImport(parent_path)
        if parent_mod:
            self.parent = __wrap__(parent_mod)
        else:
            self.parent = None
        # let's check if those must have attrs are in the context
        # for end node only, since only end node generates page
        if self.is_path_module:
            return
        must_have = self.seek(CTX_MUST_HAVE)
        if type(must_have)==types.ListType:
            # let's check if all necessary attrs are there
            for a in must_have:
                if not (a in dir(self.ctx_module)):
                    raise Exception("Must-have attribute ["+a+"] not found in context "+self.ctx_path)



    # get from self or default, but not parents
    def get(self, name):
        if name in dir(self.ctx_module):
            return __wrap__(getattr(self.ctx_module, name))
        else:
            mod = tryToImport(self.ctx_module.__name__+"."+name)
            if mod != None:
                return __wrap__(mod)
            else:
                return UNDEFINED

    # retrieve value by name, seek in parents if necessary
    def seek(self, name):
        ctx = self
        while (ctx):
            ctx_info = ctx.ctx_module.__name__ + " " + ctx.ctx_path
            # print "seeking ",name," in ",ctx_info
            value = ctx.get(name)
            if value != UNDEFINED:
                return value
            ctx = ctx.parent
        return UNDEFINED

    # parent
    def parent(self):
        return self.parent

    # return a relative path back to root (i.e. some "../..")
    def relativePathToRoot(self):
        depth = len(self.ctx_path.split("."))
        if (self.is_root):
            res = ""
        elif (self.is_path_module):
            res = string.join(['..']*depth ,'/')
        else:
            res = string.join(['..']*(depth-1),"/")
        if res == "":
            return "."
        return res

    # children modules
    def children(self):
        if self.__children__ != None:
            return self.__children__
        self.__children__ = []
        if not self.is_path_module:
            return self.__children__
        for importer, modname, ispkg in pkgutil.iter_modules(self.ctx_module.__path__):
            cmodname = string.join([self.ctx_module.__name__, modname],".")
            # print modname, self.ctx_module.__name__, cmodname
            c_module = tryToImport(cmodname, True)
            # print c_module
            self.__children__.append(__wrap__(c_module))
        return self.__children__

    # obtain context dictionary
    def getContextDict(self):
        member = {}
        # first all the sub modules
        for c in self.children():
            member[c.ctx_name] = c
        # then all the attributes, if they do not conflict
        for c in dir(self.ctx_module):
            if not (c in member.keys()):
                member[c] = getattr(self.ctx_module, c)
        return member        
        
    

# the builder to build a static web according to Mako template
class MakoStaticBuilder:
    base_dir = ""
    base_ctx = None
    template_base = ""
    context_base = ""
    output_base = ""
    # unicode handling
    i_encoding = None
    o_encoding = None
    e_error = None
    # the template lookup
    temp_lookup = None

    # the "main" method to invoke, initiate
    # local properties and start the iteration
    def __init__(self, base_dir, i_encoding='ascii', o_encoding='ascii', e_error='replace'):

        self.i_encoding = i_encoding
        self.o_encoding = o_encoding
        self.e_error = e_error
        
        base_dir = os.path.abspath(base_dir)
        print "Building Static Pages with Mako..."
        print "Base Dir:", base_dir
        print "Input Encoding:", self.i_encoding
        print "Output Encoding:", o_encoding
        print "Encoding error:", e_error
        
        self.base_dir = base_dir
        # for context, add the base_dir into system path
        if not (self.base_dir in sys.path):
            sys.path.append(self.base_dir)
        # generate all __init__.py if not provided to aboid mistakes
        self.__gen_init__(os.path.join(base_dir,ROOT_CONTEXT ))
        self.base_ctx = tryMsContext("")
        assert isinstance(self.base_ctx ,  MsContext), "ERROR: root context does not exist, check msctx_root!"

        # for template root
        self.template_base = os.path.join(base_dir, TEMPLATE_DIR)
        self.context_base = os.path.join(base_dir, ROOT_CONTEXT)        
        self.output_base = os.path.join(base_dir, OUTPUT_DIR)

        assert os.path.isdir(self.template_base)
        assert os.path.isdir(self.context_base)
        assert os.path.isdir(self.output_base)

        print "Template Base: ", self.template_base
        print "Output Base: ", self.output_base

        # examine and prepare the pathes
        assert os.path.isdir(self.template_base), "ERROR: missing template dir "+self.template_base
        self.temp_lookup = \
            TemplateLookup(directories=[self.template_base],
                           input_encoding = i_encoding,
                           output_encoding= o_encoding,
                           encoding_errors= e_error,
                           strict_undefined=True)
        if (not os.path.isdir(self.output_base)):
            print "Creating output dir"
            os.mkdir(self.output_base)
        else:
            print "Emptying output dir"
            shutil.rmtree(self.output_base)
            os.mkdir(self.output_base)

    # get template or None
    def tryTemplate(self, path):
        try:
            return self.temp_lookup.get_template(path)
        except TopLevelLookupException:
            # print e
            # traceback.print_exc()
            return None

    # iterate dir and copy resources
    def copyResource(self, base, rpath):
        spath = os.path.join(base, rpath)
        assert os.path.isdir(spath)
        for f in os.listdir(spath):
            # if another dir, step into
            src = os.path.join(spath,f)
            if os.path.isdir(src):
                self.copyResource(base, os.path.join(rpath, f))
                continue
            # file
            fparts = f.split(".")
            suffix = ""
            if len(fparts) > 1:
                suffix = fparts[-1]
                if suffix in NOT_RESOURCE_SUFFIX:
                    # print "Ignore ",src
                    continue
            # a resource, copy to putput
            outdir = os.path.join(self.output_base,rpath)
            dst = os.path.join(outdir,f)
            if not os.path.isdir(outdir):
                os.makedirs(outdir) 
            # print "Resource copying: ",src," => ",dst
            shutil.copyfile(src, dst)
    # walk all the children, so first ensure all can be imported
    def child_walk(self, node):
        children = node.children()
        for c in children:
            self.child_walk(c)

    # complete build
    def build(self):
        # recursively walk the children to make sure they all health
        self.child_walk(self.base_ctx)
        # build
        print "BUILD: Start building contexts"
        self.build_ctx(self.base_ctx)
        # copy resources
        print "BUILD: Start copying resources"
        self.copyResource(self.template_base,"")
        self.copyResource(self.context_base,"")

    def __gen_init__(self, path):
        # generate a __init__.py for every folder under context to avoid frequent problem
        has_dotpy = False
        # iterate
        for i in os.listdir(path):
            target = os.path.join(path, i)
            if os.path.isdir(target):
                self.__gen_init__(target)
            if os.path.isfile(target) and target.endswith('.py'):
                has_dotpy = True
        # generate if necessary
        target = os.path.join(path, '__init__.py')
        if has_dotpy and (not os.path.isfile(target)):
            f = open(target,'w')
            f.write("#/usr/bin/python\r\n")
            f.close()
            print "__gen_init__ created", target
        

    # start recursive building, based on context
    def build_ctx(self, msctx = None):
        assert isinstance(msctx, MsContext), "Give me a context! not a "+str(msctx)
        # print "Build [",msctx.ctx_path,']'
        
        # traverse the context tree,
        #   - build a page for every end,
        #   - step into for every path
        
        if msctx.is_path_module:
            # this is a path, iterate into all children and return
            for child in msctx.children():
                self.build_ctx(child)
            return

        # this is an end, build the page
        path_list = msctx.ctx_path.split(".")
        if len(path_list) < 2:
            basepath = ""
        else:
            basepath = ""+string.join(path_list[:-1],"/")
        if len(path_list) > 0:
            namepart = path_list[-1]
        else:
            namepart = ""
        outputdir = os.path.join(self.output_base, basepath)
        if not os.path.isdir(outputdir):
            os.makedirs(outputdir) 
        outputfile = os.path.join(outputdir, msctx.ctx_path.split(".")[-1]+PAGE_SUFFIX)
        
        # determine which template to use
        # (1) seek(MS_USETEMP), otherwise
        # (2) corresponding template in template dir
        # (3) the "path_default.html"
        template = None
        temppath = msctx.seek(MS_USETEMP)
        if temppath != UNDEFINED:
            template = self.tryTemplate(temppath)
            assert template != None, "Template from seek "+temppath+" is not available!"
            print "Choose specified template: ", template.filename
        else:
            # if the corresponding template exists
            corrpath = os.path.join("/", basepath,namepart+TEMP_SUFFIX)
            # print "[debug] search corresponding template ",corrpath
            template = self.tryTemplate(corrpath)
            if template != None:
                print "Choose corresponding template: "+template.filename
            else:
                # if there is path_default
                template = self.tryTemplate("/"+basepath+"/"+PATHDEFAULT_TEMP)
                assert template != None, "Cannot find any template for "+msctx.ctx_path
                print "Choose path default: "+"/"+basepath+"/"+PATHDEFAULT_TEMP

        # now everything is ready, render the template / context
        assert isinstance(template, Template)
        print "Build: context="+msctx.ctx_path+" template="+template.filename+" output="+outputfile
        ctxDict = msctx.getContextDict()
        # print "ctxDict[get]="+str(ctxDict.keys())
        # now add those 'reserved' variables
        ctxDict[MS_ROOT] = __wrap__(self.base_ctx)
        ctxDict[MS_SELF] = __wrap__(msctx)
        # end of 'reserved' variables
        print "Build: start rendering"
        # print "ctxDict="+str(ctxDict.keys())
        f = open(outputfile, 'w')
        f.write(template.render(**ctxDict))
        f.close()
        # print "ctxDict[AFTER]="+str(ctxDict.keys())
        print "Build: wrote to "+outputfile


usage = """ms.py [options]
    -h print this usage
    -d or --base, specify the base dir, default current path
    -i input encoding, default "ascii"
    -o output encoding, default "ascii"
    -e encoding error, default "replace"
    """


def main(argv):

    # process options and get template and context dirs
    base_dir = "."
    i_encoding = "ascii"
    o_encoding = "ascii"
    e_error = "replace"
    try:
        opts, args = getopt.getopt(argv,"hd:i:o:e:",["base="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-d", "--base"):
            base_dir = arg
        elif opt in ("-i"):
            i_encoding = arg
        elif opt in ("-o"):
            o_encoding = arg
        elif opt in ("-e"):
            e_error = arg
        
    # template dir shall be used for template lookup
    mk_builder = MakoStaticBuilder(base_dir, i_encoding=i_encoding, o_encoding=o_encoding,e_error=e_error)
    # build
    mk_builder.build()
 
# main runner
if __name__ == "__main__":
   main(sys.argv[1:])
