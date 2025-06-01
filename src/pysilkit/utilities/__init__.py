import ctypes

ct2py = lambda x: ctypes.cast(x, ctypes.POINTER(ctypes.py_object)).contents.value
py2ct = lambda x: ctypes.cast(ctypes.pointer(ctypes.py_object(x)), ctypes.c_void_p)
py2ct_pointer = lambda x: ctypes.cast(ctypes.byref(x), ctypes.c_void_p)

def auto_context(func):
    def wrapper(context, *args, **kwargs):
        py_context = ct2py(context)
        return func(py_context, *args, **kwargs)
    return wrapper