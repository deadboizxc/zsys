/*
 * bind_log.c  —  Python C binding for zsys.log
 *
 * Wraps from zsys_core.c:
 *   ansi_color, format_json_log,
 *   print_box_str, print_separator_str, print_progress_str
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/zsys_core.h"

static PyObject *
py_ansi_color(PyObject *self, PyObject *args)
{
    const char *text, *code;
    if (!PyArg_ParseTuple(args, "ss", &text, &code)) return NULL;
    char *r = zsys_ansi_color(text, code);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyObject *
py_format_json_log(PyObject *self, PyObject *args)
{
    const char *level, *message, *ts;
    if (!PyArg_ParseTuple(args, "sss", &level, &message, &ts)) return NULL;
    char *r = zsys_format_json_log(level, message, ts);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyObject *
py_print_box_str(PyObject *self, PyObject *args)
{
    const char *text; int padding;
    if (!PyArg_ParseTuple(args, "si", &text, &padding)) return NULL;
    char *r = zsys_print_box_str(text, padding);
    if (!r) return PyErr_NoMemory();
    PyObject *ret = PyUnicode_FromString(r);
    free(r);
    return ret;
}

static PyMethodDef log_methods[] = {
    {"ansi_color",      py_ansi_color,      METH_VARARGS, "Wrap text with ANSI color."},
    {"format_json_log", py_format_json_log, METH_VARARGS, "Format JSON log line."},
    {"print_box_str",   py_print_box_str,   METH_VARARGS, "Build box string."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef log_module = {
    PyModuleDef_HEAD_INIT, "_zsys_log", NULL, -1, log_methods
};

PyMODINIT_FUNC
PyInit__zsys_log(void)
{
    return PyModule_Create(&log_module);
}
