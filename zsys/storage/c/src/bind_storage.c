/*
 * bind_storage.c  —  Python C binding for zsys.storage
 *
 * Placeholder. zsys.storage is pure Python currently.
 * This file reserved for future hot paths (e.g. key serialization).
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "../include/zsys_core.h"

static PyMethodDef storage_methods[] = {
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef storage_module = {
    PyModuleDef_HEAD_INIT, "_zsys_storage", NULL, -1, storage_methods
};

PyMODINIT_FUNC
PyInit__zsys_storage(void)
{
    return PyModule_Create(&storage_module);
}
