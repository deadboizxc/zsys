/*
 * bind_utils.c  —  Python C binding for zsys.utils
 *
 * Wraps functions from zsys_core.c:
 *   escape_html, strip_html, truncate_text, split_text,
 *   get_args, format_bytes, format_duration, human_time, parse_duration,
 *   format_bold, format_italic, format_code, format_pre,
 *   format_link, format_mention, format_underline,
 *   format_strikethrough, format_spoiler, format_quote
 *
 * NOTE: These are already compiled into _zsys_core.so (monolithic).
 *       This file is for future per-module builds.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/zsys_core.h"

static PyObject *
py_escape_html(PyObject *self, PyObject *args)
{
    const char *text; Py_ssize_t len;
    if (!PyArg_ParseTuple(args, "s#", &text, &len)) return NULL;
    char *r = zsys_escape_html(text, (size_t)len);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyObject *
py_format_bytes(PyObject *self, PyObject *args)
{
    long long size;
    if (!PyArg_ParseTuple(args, "L", &size)) return NULL;
    char *r = zsys_format_bytes((int64_t)size);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyMethodDef utils_methods[] = {
    {"escape_html",   py_escape_html,   METH_VARARGS, "Escape HTML."},
    {"format_bytes",  py_format_bytes,  METH_VARARGS, "Format bytes."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef utils_module = {
    PyModuleDef_HEAD_INIT, "_zsys_utils", NULL, -1, utils_methods
};

PyMODINIT_FUNC
PyInit__zsys_utils(void)
{
    return PyModule_Create(&utils_module);
}
