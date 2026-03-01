/*
 * bind_i18n.c  —  Python C binding for zsys.i18n
 *
 * Wraps from zsys_core.c:
 *   nested_get (dict lookup by dot-separated key)
 *
 * NOTE: nested_get is in _zsys_core.c monolith currently.
 *       This file is for future per-module builds.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/zsys_core.h"

/* nested_get: dict.get("a.b.c") traversal — Python-side implementation
 * The C core doesn't have a Python dict traversal (no Python.h in zsys_core.c).
 * This binding implements it directly using CPython API. */
static PyObject *
py_nested_get(PyObject *self, PyObject *args)
{
    PyObject *data;
    const char *key;
    PyObject *fallback = Py_None;
    if (!PyArg_ParseTuple(args, "Os|O", &data, &key, &fallback)) return NULL;

    PyObject *current = data;
    char buf[256];
    const char *p = key;
    while (*p) {
        const char *dot = strchr(p, '.');
        size_t part_len;
        if (dot) {
            part_len = (size_t)(dot - p);
            if (part_len >= sizeof(buf)) { Py_INCREF(fallback); return fallback; }
            memcpy(buf, p, part_len);
            buf[part_len] = '\0';
            p = dot + 1;
        } else {
            part_len = strlen(p);
            if (part_len >= sizeof(buf)) { Py_INCREF(fallback); return fallback; }
            memcpy(buf, p, part_len);
            buf[part_len] = '\0';
            p += part_len;
        }
        if (!PyDict_Check(current)) { Py_INCREF(fallback); return fallback; }
        PyObject *k = PyUnicode_FromString(buf);
        if (!k) return NULL;
        PyObject *next = PyDict_GetItem(current, k);
        Py_DECREF(k);
        if (!next) { Py_INCREF(fallback); return fallback; }
        current = next;
    }
    Py_INCREF(current);
    return current;
}

static PyMethodDef i18n_methods[] = {
    {"nested_get", py_nested_get, METH_VARARGS, "Get nested dict value by dot-key."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef i18n_module = {
    PyModuleDef_HEAD_INIT, "_zsys_i18n", NULL, -1, i18n_methods
};

PyMODINIT_FUNC
PyInit__zsys_i18n(void)
{
    return PyModule_Create(&i18n_module);
}
