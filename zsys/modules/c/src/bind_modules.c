/*
 * bind_modules.c  —  Python C binding for zsys.modules
 *
 * Wraps from zsys_core.c:
 *   parse_meta_comments, build_help_text, match_prefix
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/zsys_core.h"

static PyObject *
py_parse_meta_comments(PyObject *self, PyObject *args)
{
    const char *source; Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "s#", &source, &len)) return NULL;
    char **pairs = zsys_parse_meta_comments(source, (size_t)len);
    if (!pairs) Py_RETURN_NONE;
    PyObject *d = PyDict_New();
    for (int i = 0; pairs[i] && pairs[i+1]; i += 2) {
        PyObject *k = PyUnicode_FromString(pairs[i]);
        PyObject *v = PyUnicode_FromString(pairs[i+1]);
        if (k && v) PyDict_SetItem(d, k, v);
        Py_XDECREF(k); Py_XDECREF(v);
    }
    zsys_meta_free(pairs);
    return d;
}

static PyObject *
py_build_help_text(PyObject *self, PyObject *args)
{
    const char *name, *prefix;
    PyObject *cmds_list;
    if (!PyArg_ParseTuple(args, "sOs", &name, &cmds_list, &prefix)) return NULL;
    Py_ssize_t n = PyList_Size(cmds_list);
    const char **cmds = calloc(n + 1, sizeof(char *));
    if (!cmds) return PyErr_NoMemory();
    for (Py_ssize_t i = 0; i < n; i++) {
        PyObject *item = PyList_GetItem(cmds_list, i);
        cmds[i] = PyUnicode_AsUTF8(item);
    }
    cmds[n] = NULL;
    char *r = zsys_build_help_text(name, cmds, prefix);
    free(cmds);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyMethodDef modules_methods[] = {
    {"parse_meta_comments", py_parse_meta_comments, METH_VARARGS, "Parse module meta."},
    {"build_help_text",     py_build_help_text,     METH_VARARGS, "Build help text."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef modules_module = {
    PyModuleDef_HEAD_INIT, "_zsys_modules", NULL, -1, modules_methods
};

PyMODINIT_FUNC
PyInit__zsys_modules(void)
{
    return PyModule_Create(&modules_module);
}
