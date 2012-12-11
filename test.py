# test functionality of MakoStatic and show how it works (and should work)
import ms
from ms import MsContext
import traceback
from mako.runtime import UNDEFINED
import sys
import os
import os.path

# test MsContext

def exectest_all(expr_array):
    for test in expr_array:
        exectest(test)

def exectest(expr):
    try:
        exec expr
        print "Test: ", expr, " PASSED"
    except:
        print "Test: ", expr, " FAILED!!"
        traceback.print_exc()


print "Starting MsContext test"
sys.path.append(os.path.abspath("test"))
import msctx_root

ms_test = MsContext(msctx_root)

print "Testing root context"
exectest_all([
    "assert ms_test.ctx_module == msctx_root",
    "assert ms_test.parent == None",
    "assert ms_test.is_path_module",
    "assert ms_test.ctx_path == ''",
    "assert ms_test.ctx_name == ''",
    "assert ms_test.is_root",
    "assert ms_test.relativePathToRoot() == '.'"
    ])

print "Testing children of root context"
children = ms_test.children()
exectest_all([
    "assert len(children) == 2",
    "assert 'msctx_root.end1' in map(lambda x:x.ctx_module.__name__, children)",
    "assert 'msctx_root.path1' in map(lambda x:x.ctx_module.__name__, children)"
    ])

print "Testing get and seek of root context"
exectest_all([
    "assert ms_test.get('test_seek1') == 'test_seek1 from test/root_context'",
    "assert ms_test.get('test_end1_value1') == 'test_end1_value1 from test/root_context'",
    "assert ms_test.get('test_p1_seekp1') == 'test_p1_seekp1 from test/root_context'",
    "assert ms_test.get('test_p1_value1') == 'test_p1_value1 from test/root_context'",
    "assert ms_test.seek('test_seek1') == 'test_seek1 from test/root_context'",
    "assert ms_test.seek('test_end1_value1') == 'test_end1_value1 from test/root_context'",
    "assert ms_test.seek('test_p1_seekp1') == 'test_p1_seekp1 from test/root_context'",
    "assert ms_test.seek('test_p1_value1') == 'test_p1_value1 from test/root_context'"
    ])
    
print "Testing end1 context"
end1 = filter(lambda x:x.ctx_path=="end1", children)[0]
import msctx_root.end1
exectest_all([
    "assert end1.ctx_module == msctx_root.end1",
    "assert end1.parent == ms_test",
    "assert not end1.is_path_module",
    "assert end1.ctx_path == 'end1'",
    "assert end1.ctx_name == 'end1'",
    "assert not end1.is_root",
    "assert len(end1.children()) == 0",
    "assert end1.relativePathToRoot() == '.'"
    ])

print "Testing get and seek of end1 context"
exectest_all([
    "assert end1.get('test_seek1') == UNDEFINED",
    "assert end1.get('test_end1_value1') == 'test_end1_value1 from test/end1'",
    "assert end1.get('test_p1_seekp1') == 'test_p1_seekp1 from test/end1'",
    "assert end1.get('test_p1_value1') == 'test_p1_value1 from test/end1'",
    "assert end1.seek('test_seek1') == 'test_seek1 from test/root_context'",
    "assert end1.seek('test_end1_value1') == 'test_end1_value1 from test/end1'",
    "assert end1.seek('test_p1_seekp1') == 'test_p1_seekp1 from test/end1'",
    "assert end1.seek('test_p1_value1') == 'test_p1_value1 from test/end1'"
    ])


print "Testing path1 context"
path1 = filter(lambda x:x.ctx_path=="path1", children)[0]

import msctx_root.path1
exectest_all([
    "assert path1.ctx_module == msctx_root.path1",
    "assert path1.parent == ms_test",
    "assert path1.is_path_module",
    "assert path1.ctx_path == 'path1'",
    "assert path1.ctx_name == 'path1'",
    "assert not path1.is_root",
    "assert path1.relativePathToRoot() == '..'",
    "assert len(path1.children()) == 4"])

print "Testing get and seek of path1 context"
exectest_all([
    "assert path1.get('test_seek1') == UNDEFINED",
    "assert path1.get('test_end1_value1') == UNDEFINED",
    "assert path1.get('test_p1_seekp1') == 'test_p1_seekp1 from test/path1/__init__'",
    "assert path1.get('test_p1_value1') == 'test_p1_value1 from test/path1/__init__'",
    "assert path1.seek('test_seek1') == 'test_seek1 from test/root_context'",
    "assert path1.seek('test_end1_value1') == 'test_end1_value1 from test/root_context'",
    "assert path1.seek('test_p1_seekp1') == 'test_p1_seekp1 from test/path1/__init__'",
    "assert path1.seek('test_p1_value1') == 'test_p1_value1 from test/path1/__init__'",
    "assert path1.parent == ms_test"
    ])

print "Testing path1/p1e1 context"
p1e1 = filter(lambda x:x.ctx_path=="path1.p1e1", path1.children())[0]
import msctx_root.path1.p1e1
exectest_all([
    "assert p1e1.ctx_module == msctx_root.path1.p1e1",
    "assert p1e1.parent == path1",
    "assert not p1e1.is_path_module",
    "assert p1e1.ctx_path == 'path1.p1e1'",
    "assert p1e1.ctx_name == 'p1e1'",
    "assert not p1e1.is_root",
    "assert len(p1e1.children()) == 0",
    "assert path1.parent == ms_test",
    "assert p1e1.relativePathToRoot() == '..'"
    ])

print "Testing get and seek of path1/p1e1 context"

exectest_all([
    "assert p1e1.get('test_seek1') == UNDEFINED",
    "assert p1e1.get('test_end1_value1') == UNDEFINED",
    "assert p1e1.get('test_p1_seekp1') == UNDEFINED",
    "assert p1e1.get('test_p1_value1') == 'test_p1_value1 from test/path1/p1e1'",
    "assert p1e1.seek('test_seek1') == 'test_seek1 from test/root_context'",
    "assert p1e1.seek('test_end1_value1') == 'test_end1_value1 from test/root_context'",
    "assert p1e1.seek('test_p1_seekp1') == 'test_p1_seekp1 from test/path1/__init__'",
    "assert p1e1.seek('test_p1_value1') == 'test_p1_value1 from test/path1/p1e1'"
    ])

print "Testing getMakoBufContext"
ctxdict = ms_test.getContextDict()
exectest_all([
    "assert ctxdict['end1'] == end1",
    "assert ctxdict['path1'] == path1",
    "assert ctxdict['path1'].get('p1e1') == p1e1"
    ])

print
print
print
print "Now try the building"
mk_builder = ms.MakoStaticBuilder("test")
mk_builder.build()
