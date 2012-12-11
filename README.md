#MakoStatic
==========

    Mako is a template system based on python, see: 

    http://www.makotemplates.org/

    While I have a need to build a static web - all static pages, with the help of a template system. 
    MakoStatic (MS) is a tool to generate static website from a collection of data and
    some Mako Templates.

__Below explains the idea:__

    - follow the MVC approach, separate Control, Model and View
    - Model is python module to put contents, for example your news article
    - View is Mako Templates
    - Since this is static web builder, there is no much need for controller. 
    - [Todo] Maybe there is need for some pre-processing controller to process Model before sending to View. 

__Dir structure:__

    root: just create a dir as root for your static web
    root/template: where "View", i.e. MakoTemplates were put
    root/msctx_root: where "Model" is put, will explain further
    root/output: DO NOT put anything here, everything will be wiped out when building your web. 

##USAGE
===========

###Model

    Your static web has a structure, there is paths and pages. So do python modules. MS will first add your 
    project root into sys.path, so your module msctx_root can be imported and traversed by MS. Then the structure
    of your msctx_root and the static website to be generated has such connection:

    msctx_root => "/"
    msctx_root/index.py => "/index.html"
    msctx_root/news/ms_static_released.py => "/news/ms_static_released.html"

###Generation:

    To use mako static, just run it from command line. Here is usage:

        ms.py [options]
            -h print this usage
            -d or --base, specify the base dir, default current path
            -i input encoding, default "ascii"
            -o output encoding, default "ascii"
            -e encoding error, default "replace"

    The engine will buid the web as follows:

    (1) it traverse and msctx_root dir and add those missing "__init__.py"... for convenience

    (2) it traverse msctx_root and load all the python modules. this is to make sure the "Model" are all ok before building,
    save from passing the wrong thing in template render, which makes debugging difficult
    (3) it traverse again msctx_root, this time actually build the pages, see below.
    (4) finally, it traver both template and msctx_root, searching anything not a template (not .html) and not a python 
    module (.py), copy them to the corresponding output dir

###Page Building:

    For each "end module", such as msctx_root/something/end_module.py, a corresponding html page will be built from a Mako 
    Template, given the end_module as its context. 

    Page Building / context:

    An end module is first a python module, but as simple as possible, usually just some data, for example this one:

    #end_module.py
    title = "Mako Static Released"
    content = "This is a small tool helping to build static pages"

###Page Building / seeking template:

    Engine find the template for building an end_module in the following manner:
    (1) use a template if specified explicitly, by calling "the_module.seek("MS_USE_TEMPLATE")" (seek method will explain
        below); otherwise
    (2) look at a corresponding template 
            root/msctx_root/something/end_module.py corresponds to 
            root/template/something/end_module.html
        ; or, as last resort:
    (3) look at a corresponding "path_default.html" template 
            root/msctx_root/something/end_module.py -> 
            root/msctx_root/something/path_default.html

    Once a template is found, engine pass data in the end_module as the context to the template, generate the page and write
    the page to the corresponding output dir. So root/msctx_root/something/end_module.py -> root/output/something/end_module.html

###Page Building / What is Given to Template

    (1) all the members of the end_module, if they are string, int, and everything, except for
    (2) all the children of the end_module, if they are module, then wrapped as a MsContext (see below)
    (3) ms_root, the root module, i.e. msctx_root, but wrapped as a MsContext
    (4) ms_self, this module wrapped as a MsContext

###MsContext

    - children() : return all child modules, wrapped as MsContext, in a list
    - relativePathToRoot(): return the relative path to root, so for root/msctx_root/something/end_module.py 
      this is ".."; for root and first layer, this results "."; useful for generating relative path
    - parent() or parent : the parent module, as MsContext
    - get(name) : get the member, or a child module wrapped as MsContext, by the name
    - seek(name) : this one is interesting: it try to get the name from this module, or the parent, or parent's 
      parent, until UNDEFINED is returned
    - ctx_module : the python module being wrapped in
    - ctx_path : name of the python module from root, for the above example, "something.end_module"
    - ctx_name : just the last part of ctx_path
    - is_path_module : not end module, for example "something"
    - is_root : is root?

###Check before Render
    
    I find, however, once control is passed to render, everything become somewhat mysterious. For example, name error 
    hardly tell you anything about what's wrong, and python block aren't really python if you do extreme python things.
    I decide to check as much as possible before entering the render template stage. Also, my experience is to add one
    directive at a time and test, so you know where goes wrong.

    Here is the checks will be made:

    (1) walk the model to make sure they loads
    (2) add __init__.py to those module folder that should have one; the engine is smart enough not to over-ride one
    already there
    (3) if end_module.seek("CTX_MUST_HAVE") returns some non-empty list of strings, engine will check to make sure the module has
    all the members specified in the list.

