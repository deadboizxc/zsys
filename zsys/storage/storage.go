// Package storage provides key-value storage abstractions for zsys.
// Go equivalent of zsys.storage (Python).
package storage

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "sync"
    _ "modernc.org/sqlite"
)

// Storage is a generic key-value store interface.
type Storage interface {
    Get(key string, dest interface{}) error
    Set(key string, value interface{}) error
    Delete(key string) error
    Keys(pattern string) ([]string, error)
    Close() error
}

// SQLiteStorage implements Storage using SQLite.
type SQLiteStorage struct {
    mu  sync.RWMutex
    db  *sql.DB
}

// NewSQLite opens (or creates) a SQLite storage at path.
func NewSQLite(path string) (*SQLiteStorage, error) {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, fmt.Errorf("zsys/storage: open %s: %w", path, err)
    }
    _, err = db.Exec(`CREATE TABLE IF NOT EXISTS kv (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )`)
    if err != nil {
        db.Close()
        return nil, err
    }
    return &SQLiteStorage{db: db}, nil
}

func (s *SQLiteStorage) Set(key string, value interface{}) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }
    s.mu.Lock()
    defer s.mu.Unlock()
    _, err = s.db.Exec(
        `INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`,
        key, string(data))
    return err
}

func (s *SQLiteStorage) Get(key string, dest interface{}) error {
    s.mu.RLock()
    defer s.mu.RUnlock()
    var raw string
    err := s.db.QueryRow(`SELECT value FROM kv WHERE key=?`, key).Scan(&raw)
    if err == sql.ErrNoRows {
        return fmt.Errorf("key not found: %s", key)
    }
    if err != nil {
        return err
    }
    return json.Unmarshal([]byte(raw), dest)
}

func (s *SQLiteStorage) Delete(key string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    _, err := s.db.Exec(`DELETE FROM kv WHERE key=?`, key)
    return err
}

func (s *SQLiteStorage) Keys(pattern string) ([]string, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    rows, err := s.db.Query(`SELECT key FROM kv WHERE key LIKE ?`, pattern)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var keys []string
    for rows.Next() {
        var k string
        if err := rows.Scan(&k); err != nil {
            return nil, err
        }
        keys = append(keys, k)
    }
    return keys, rows.Err()
}

func (s *SQLiteStorage) Close() error {
    return s.db.Close()
}
