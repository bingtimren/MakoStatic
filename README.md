MakoStatic
==========

Mako is a template system based on python, see: 

http://www.makotemplates.org/

While I have a need to build a static web - all static pages, with the help of a template system. 
MakoStatic (MS) is a tool to generate static website from a collection of data and
some Mako Templates.

Below explains the idea:

- follow the MVC approach, separate Control, Model and View
- Model is python module to put contents, for example your news article
- View is Mako Templates
- Since this is static web builder, there is no much need for controller. 
- [Todo] Maybe there is need for some pre-processing controller to process Model before sending to View. 

Dir structure:

root: just create a dir as root for your static web
root/template: where "View", i.e. MakoTemplates were put
root/msctx_root: where "Model" is put, will explain further
root/output: DO NOT put anything here, everything will be wiped out when building your web. 

USAGE
===========

(1) Model

Your static web has a structure, there is paths and pages. So do python modules. MS will first add your 
project root into sys.path, so your module msctx_root can be imported and traversed by MS. Then the structure
of your msctx_root and the static website to be generated has such connection:

msctx_root => "/"
msctx_root/index.py => "/index.html"
msctx_root/news/ms_static_released.py => "/news/ms_static_released.html"

Generation:

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

Page Building:

For each "end module", such as msctx_root/something/end_module.py, a corresponding html page will be built from a Mako 
Template and the end_module. 

An end module is usually just some data, for example this one:

#end_module.py
title = "Mako Static Released"
content = "This is a small tool helping to build static pages"

Page Building - seeking template:

Engine find the template for building an end_module in the following manner:
(1) use a template if specified explicitly; otherwise
(2) look at a corresponding template 
        root/msctx_root/something/end_module.py corresponds to 
            root/template/something/end_module.html
    ; if not found, then
(3) look at a "path_default.html" template 
        root/msctx_root/something/end_module.py -> 
            root/msctx_root/something/path_default.html

Resource: 
Anything put under context and not a ".py" is copied to output path


The Engine:
All engine needs is the base dir
Engine iterates the template dir, and
for all_children.html, iterates all .py and generates one page for each of them using path_default.html as template
for other .html templates, generate with / without the corresponding context
Template, being rendered, expects to find following from its context
values in the corresponding context
"ms" the MsContext, which provides access to the whole context graph
MsContext: provides access to the context
each module is a MsContext
children - a list containing all the children, each a MsContext
parent - the parent
get('name') - retrieves value or sub-module, from this module or path_default, return UNDEFINED if not found
seek('name') - like get, but seek from parents if not found, return UNDEFINED if not found

