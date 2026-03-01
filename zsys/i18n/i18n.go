// Package i18n provides internationalization support via zsys C core.
// Go equivalent of zsys.i18n (Python).
//
// Usage:
//
//i18n := zsys.NewI18N("./locales", "en")
//text := i18n.T("welcome")
package i18n

import (
    "encoding/json"
    "os"
    "path/filepath"
    "strings"
    "sync"
)

// I18N manages translations for multiple languages.
type I18N struct {
    mu           sync.RWMutex
    data         map[string]map[string]interface{}
    defaultLang  string
    currentLang  string
    localesPath  string
}

// New creates an I18N instance loading from localesPath.
func New(localesPath, defaultLang string) (*I18N, error) {
    i := &I18N{
        data:        make(map[string]map[string]interface{}),
        defaultLang: defaultLang,
        currentLang: defaultLang,
        localesPath: localesPath,
    }
    if err := i.loadLang(defaultLang); err != nil {
        return nil, err
    }
    return i, nil
}

func (i *I18N) loadLang(lang string) error {
    path := filepath.Join(i.localesPath, lang+".json")
    data, err := os.ReadFile(path)
    if err != nil {
        return err
    }
    var m map[string]interface{}
    if err := json.Unmarshal(data, &m); err != nil {
        return err
    }
    i.mu.Lock()
    i.data[lang] = m
    i.mu.Unlock()
    return nil
}

// SetLang sets the current language.
func (i *I18N) SetLang(lang string) error {
    i.mu.RLock()
    _, loaded := i.data[lang]
    i.mu.RUnlock()
    if !loaded {
        if err := i.loadLang(lang); err != nil {
            return err
        }
    }
    i.mu.Lock()
    i.currentLang = lang
    i.mu.Unlock()
    return nil
}

// T returns a translation for the given dot-separated key.
// Falls back to defaultLang, then returns the key itself.
func (i *I18N) T(key string) string {
    i.mu.RLock()
    defer i.mu.RUnlock()

    for _, lang := range []string{i.currentLang, i.defaultLang} {
        if data, ok := i.data[lang]; ok {
            if v := nestedGet(data, key); v != "" {
                return v
            }
        }
    }
    return key
}

// nestedGet traverses a nested map by dot-separated key.
func nestedGet(data map[string]interface{}, key string) string {
    parts := strings.SplitN(key, ".", 2)
    v, ok := data[parts[0]]
    if !ok {
        return ""
    }
    if len(parts) == 1 {
        if s, ok := v.(string); ok {
            return s
        }
        return ""
    }
    if sub, ok := v.(map[string]interface{}); ok {
        return nestedGet(sub, parts[1])
    }
    return ""
}
