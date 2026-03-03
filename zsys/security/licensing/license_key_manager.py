"""Legacy license key manager — RSA-signed, AES-encrypted license keys.

Low-level cryptographic license key generation, HMAC verification, and RSA digital
signatures using pycryptodome. This module is superseded by LicenseManager in
manager.py but is kept for backward compatibility.
Requires: pip install pycryptodome.
"""

# RU: Устаревший менеджер лицензионных ключей с RSA-подписью и AES-шифрованием.
# RU: Заменён LicenseManager в manager.py, сохранён для обратной совместимости.
import os
import base64
import hashlib
import hmac
import struct
import uuid
from datetime import datetime, timedelta
from hashlib import sha512

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA512, HMAC
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# Хеширование данных (без соли)
def hash_data(data):
    """
    Хеширование данных с использованием SHA-512.
    :param data: Данные для хеширования (байты).
    :return: Хешированные данные (байты).
    """
    return hashlib.sha512(data).digest()


# Шифрование данных с использованием AES
def encrypt_data(data, key):
    """
    Шифрование данных с использованием AES.
    :param data: Данные для шифрования (байты).
    :param key: Ключ шифрования (байты).
    :return: Зашифрованные данные (байты).
    """
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes


# Дешифрование данных с использованием AES
def decrypt_data(encrypted_data, key):
    """
    Дешифрование данных с использованием AES.
    :param encrypted_data: Зашифрованные данные (байты).
    :param key: Ключ шифрования (байты).
    :return: Расшифрованные данные (байты).
    """
    iv = encrypted_data[: AES.block_size]
    ct = encrypted_data[AES.block_size :]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)


# Генерация HMAC
def generate_hmac(data, key):
    """
    Генерация HMAC для данных.
    :param data: Данные для HMAC (байты).
    :param key: Ключ для HMAC (байты).
    :return: HMAC (байты).
    """
    return HMAC.new(key, data, digestmod=sha512).digest()


# Проверка HMAC
def verify_hmac(data, hmac_value, key):
    """
    Проверка HMAC для данных.
    :param data: Данные для проверки (байты).
    :param hmac_value: Ожидаемый HMAC (байты).
    :param key: Ключ для HMAC (байты).
    :return: True, если HMAC совпадает, иначе False.
    """
    return hmac.compare_digest(generate_hmac(data, key), hmac_value)


# Генерация главного ключа
def generate_main_key(file_name, suffix="bin"):
    """
    Генерация главного ключа и его сохранение в файл.
    :param file_name: Имя файла для сохранения.
    :param suffix: Расширение файла ("bin" или "txt").
    """
    full_file_name = f"{file_name}.{suffix}"

    # Генерация ключа
    main_key = os.urandom(512)  # Генерация случайных байтов

    # Сохранение ключа
    if suffix == "txt":
        main_key = base64.b64encode(main_key).decode(
            "utf-8"
        )  # Кодировка в Base64 для текстового формата
        with open(full_file_name, "w") as f:
            f.write(main_key)
    else:
        with open(full_file_name, "wb") as f:
            f.write(main_key)
    print(f"Главный ключ сохранён в {full_file_name}.")


# Расчет времени истечения срока действия
def calculate_expiration(duration_str):
    """
    Расчет времени истечения срока действия лицензии.
    :param duration_str: Строка с продолжительностью (например, "1y", "2m", "30d").
    :return: Время истечения срока действия (timestamp).
    """
    duration = parse_duration(duration_str)
    expiration_time = int((datetime.now() + duration).timestamp())
    return expiration_time


# Разбор строки с продолжительностью
def parse_duration(duration_str):
    """Parse a compact duration string into a :class:`timedelta`.

    Recognises the following unit suffixes: ``y`` (year = 365 days),
    ``m`` (month = 30 days), ``d`` (day).  Multiple units may be combined,
    e.g. ``"1y2m30d"``.

    Args:
        duration_str: Duration string such as ``"1y"``, ``"30d"``, or
            ``"1y2m30d"``.

    Returns:
        :class:`datetime.timedelta` representing the total duration.
    """
    # RU: Regex ищет пары (число, единица); y=365d, m=30d; суммирует timedelta.
    import re

    pattern = re.compile(r"(\d+)([ymd])")
    match = pattern.findall(duration_str)
    duration = timedelta(days=0)

    for value, unit in match:
        value = int(value)
        if unit == "y":
            duration += timedelta(days=value * 365)
        elif unit == "m":
            duration += timedelta(days=value * 30)
        elif unit == "d":
            duration += timedelta(days=value)

    return duration


# Генерация лицензионного ключа с user_id и UUID
def generate_license_key(
    main_key_file,
    license_key_file,
    hash_storage_file,
    duration_str,
    user_id,
    suffix="bin",
):
    """Generate, hash, and persist a license key for a user.

    Reads the main key from *main_key_file*, computes an expiration timestamp,
    generates a UUID, assembles ``user_id + main_key + UUID + expiration``,
    hashes the result with :func:`hash_data`, saves the raw key data to
    *license_key_file*, and appends the hash to *hash_storage_file* via
    :func:`save_hash_to_storage`.

    Args:
        main_key_file: Path to the main key file (binary format).
        license_key_file: Base name for the output license key file.
        hash_storage_file: Base name of the shared hash storage file.
        duration_str: Duration string, e.g. ``"1y"`` or ``"30d"``.
        user_id: Unique user identifier string embedded in the key.
        suffix: ``"bin"`` for binary output; ``"txt"`` for Base64 text.
    """
    # RU: user_id+main_key+UUID+expiration → hash_data → сохраняет ключ и хеш в файлы.
    full_license_key_file = f"{license_key_file}.{suffix}"

    # Чтение главного ключа
    with open(main_key_file, "rb") as file:
        main_key = file.read()

    # Расчет времени истечения срока действия
    expiration_time = calculate_expiration(duration_str)

    # Генерация UUID для лицензии
    license_uuid = uuid.uuid4().bytes

    # Формирование лицензионного ключа (main_key + user_id + UUID + expiration_time)
    license_key_data = (
        user_id.encode("utf-8")  # user_id (в байтах)
        + main_key  # Главный ключ (512 байт)
        + license_uuid  # UUID (16 байт)
        + struct.pack("I", expiration_time)  # Время истечения (4 байта)
    )

    # Хеширование лицензионного ключа
    license_key_hash = hash_data(
        license_key_data
    )  # Используем hash_data вместо hash_with_salt

    # Сохранение лицензионного ключа в отдельный файл
    if suffix == "txt":
        license_key_data = base64.b64encode(license_key_data).decode("utf-8")
        with open(full_license_key_file, "w") as file:
            file.write(license_key_data)
    else:
        with open(full_license_key_file, "wb") as file:
            file.write(license_key_data)

    # Сохранение хеша в общий файл
    save_hash_to_storage(hash_storage_file, license_key_file, license_key_hash, suffix)

    print(f"Лицензионный ключ сохранён в {full_license_key_file}.")


# Сохранение хеша в общий файл
def save_hash_to_storage(hash_storage_file, key_name, key_hash, suffix="bin"):
    """Append a license key hash to the shared hash storage file.

    Args:
        hash_storage_file: Base name of the shared hash storage file.
        key_name: Human-readable key identifier used only for logging.
        key_hash: Binary hash bytes to store.
        suffix: ``"bin"`` appends raw bytes (``"ab"`` mode); ``"txt"``
            appends a Base64-encoded line (``"a"`` mode).
    """
    # RU: "txt" → Base64 строка (append "a"); "bin" → бинарный append ("ab").
    full_hash_storage_file = f"{hash_storage_file}.{suffix}"

    if suffix == "txt":
        # Сохраняем хеш в текстовом формате (Base64)
        key_hash_base64 = base64.b64encode(key_hash).decode("utf-8")
        with open(
            full_hash_storage_file, "a"
        ) as file:  # 'a' для добавления в конец файла
            file.write(f"{key_hash_base64}\n")
    else:
        # Сохраняем хеш в бинарном формате
        with open(
            full_hash_storage_file, "ab"
        ) as file:  # 'ab' для добавления в бинарном режиме
            file.write(key_hash)

    print(f"Хеш для ключа '{key_name}' добавлен в {full_hash_storage_file}.")
    print(
        f"Хеш (в Base64): {base64.b64encode(key_hash).decode('utf-8')}"
    )  # Отладочная информация


# Проверка лицензии с user_id и UUID
def check_license(license_key_file, hash_storage_file, user_id, suffix="bin"):
    """Validate a license key file against the hash storage.

    Reads and optionally Base64-decodes the license key, extracts the
    embedded *user_id* and UUID, recomputes the SHA-512 hash with
    :func:`hash_data`, looks up the hash in *hash_storage_file*, and
    checks the expiration timestamp in the final 4 bytes.

    Args:
        license_key_file: Full path to the license key file.
        hash_storage_file: Full path to the shared hash storage file.
        user_id: Expected user identifier to verify ownership.
        suffix: ``"bin"`` for binary files; ``"txt"`` for Base64 text.

    Returns:
        Tuple of ``(is_valid: bool, expiration_date: str | None)`` where
        *expiration_date* is formatted as ``"YYYY-MM-DD"`` when available.
    """
    # RU: Читает ключ → извлекает user_id/UUID → recomputes hash → проверяет срок действия.
    try:
        # Чтение лицензионного ключа
        with open(license_key_file, "rb" if suffix == "bin" else "r") as file:
            license_key_data = file.read()
            if suffix == "txt":
                license_key_data = base64.b64decode(license_key_data)

        # Извлечение user_id и UUID из лицензионного ключа
        user_id_length = len(user_id.encode("utf-8"))  # Длина user_id в байтах
        user_id_from_key = license_key_data[512 : 512 + user_id_length].decode(
            "utf-8"
        )  # Извлечение user_id
        license_uuid = license_key_data[  # noqa: F841
            512 + user_id_length : 528 + user_id_length
        ]  # Извлечение UUID

        # Проверка user_id
        if user_id_from_key != user_id:
            print(f"❌ Лицензия не принадлежит пользователю {user_id}!")
            return False, None

        # Хеширование текущего ключа
        current_hash = hash_data(
            license_key_data
        )  # Используем hash_data вместо hash_with_salt
        print(
            f"Текущий хеш (в Base64): {base64.b64encode(current_hash).decode('utf-8')}"
        )  # Отладочная информация

        # Чтение хешей из общего файла
        with open(hash_storage_file, "rb" if suffix == "bin" else "r") as file:
            if suffix == "txt":
                stored_hashes = file.readlines()
                stored_hashes = [
                    base64.b64decode(line.strip()) for line in stored_hashes
                ]
            else:
                stored_hashes = file.read()
                hash_length = 64  # Длина хеша SHA-512
                stored_hashes = [
                    stored_hashes[i : i + hash_length]
                    for i in range(0, len(stored_hashes), hash_length)
                ]

        # Проверка хеша
        if current_hash in stored_hashes:
            expiration_time = struct.unpack("I", license_key_data[-4:])[0]
            current_time = int(datetime.now().timestamp())
            expiration_date = datetime.fromtimestamp(expiration_time).strftime(
                "%Y-%m-%d"
            )
            if current_time > expiration_time:
                print(f"❌ Лицензия просрочена! Дата окончания: {expiration_date}")
                return False, expiration_date
            else:
                print(f"✅ Лицензия действительна. Дата окончания: {expiration_date}")
                return True, expiration_date
        else:
            print("❌ Хеш лицензионного ключа не найден в общем файле!")
            print(
                f"Сохранённые хеши: {[base64.b64encode(h).decode('utf-8') for h in stored_hashes]}"
            )  # Отладочная информация
            return False, None
    except Exception as e:
        print(f"Ошибка при проверке лицензии: {e}")
        return False, None


# Генерация ключей RSA
def generate_rsa_keys(public_key_file, private_key_file):
    """Generate a 2048-bit RSA key pair and save both keys as PEM files.

    Args:
        public_key_file: Destination path for the PEM-encoded public key.
        private_key_file: Destination path for the PEM-encoded private key.
    """
    # RU: RSA-2048; сохраняет PEM-файлы публичного и приватного ключей.
    key = RSA.generate(2048)
    with open(public_key_file, "wb") as pub_file:
        pub_file.write(key.publickey().export_key())
    with open(private_key_file, "wb") as priv_file:
        priv_file.write(key.export_key())
    print(f"Публичный ключ сохранён в {public_key_file}.")
    print(f"Приватный ключ сохранён в {private_key_file}.")


# Генерация цифровой подписи
def generate_signature(data, private_key_file, signature_file, suffix="bin"):
    """Sign *data* with RSA PKCS1v15 + SHA-512 and save the signature.

    Args:
        data: Bytes to sign.
        private_key_file: Path to the PEM private key file.
        signature_file: Base name for the output signature file.
        suffix: ``"bin"`` saves raw bytes; ``"txt"`` saves Base64 text.

    Raises:
        FileNotFoundError: When *private_key_file* does not exist.
    """
    # RU: RSA PKCS1v15 + SHA512; "txt" → Base64; "bin" → бинарный файл.
    # Проверка существования файла с приватным ключом
    if not os.path.exists(private_key_file):
        raise FileNotFoundError(
            f"Файл с приватным ключом {private_key_file} не найден."
        )

    with open(private_key_file, "rb") as file:
        private_key = RSA.import_key(file.read())

    # Генерация подписи
    h = SHA512.new(data)
    signature = pkcs1_15.new(private_key).sign(h)

    # Сохранение подписи
    if suffix == "txt":
        # Сохранение в текстовом формате (Base64)
        signature_base64 = base64.b64encode(signature).decode("utf-8")
        with open(f"{signature_file}.{suffix}", "w") as file:
            file.write(signature_base64)
    else:
        # Сохранение в бинарном формате
        with open(f"{signature_file}.{suffix}", "wb") as file:
            file.write(signature)
    print(f"Цифровая подпись сохранена в {signature_file}.{suffix}.")


# Проверка цифровой подписи
def verify_signature(data, signature_file, public_key_file, suffix="bin"):
    """Verify an RSA PKCS1v15 + SHA-512 signature against *data*.

    Args:
        data: Bytes whose authenticity is being verified.
        signature_file: Full path to the signature file (including extension).
        public_key_file: Path to the PEM public key file.
        suffix: ``"bin"`` reads raw bytes; ``"txt"`` reads Base64 text.

    Returns:
        ``True`` if the signature is valid; ``False`` otherwise.

    Raises:
        FileNotFoundError: When *public_key_file* or *signature_file* does
            not exist.
    """
    # RU: RSA PKCS1v15 + SHA512; читает подпись (bin или Base64 txt); возвращает bool.
    # Проверка существования файлов
    if not os.path.exists(public_key_file):
        raise FileNotFoundError(f"Файл с публичным ключом {public_key_file} не найден.")
    if not os.path.exists(signature_file):
        raise FileNotFoundError(f"Файл с подписью {signature_file} не найден.")

    with open(public_key_file, "rb") as file:
        public_key = RSA.import_key(file.read())

    # Чтение подписи из файла
    if suffix == "txt":
        # Чтение подписи в текстовом формате (Base64)
        with open(signature_file, "r") as file:
            signature_base64 = file.read()
            signature = base64.b64decode(signature_base64)
    else:
        # Чтение подписи в бинарном формате
        with open(signature_file, "rb") as file:
            signature = file.read()

    # Проверка подписи
    h = SHA512.new(data)
    try:
        pkcs1_15.new(public_key).verify(h, signature)
        print("✅ Цифровая подпись действительна.")
        return True
    except (ValueError, TypeError):
        print("❌ Цифровая подпись недействительна.")
        return False


# Основной блок
if __name__ == "__main__":
    # Пример использования
    main_key_file = "main_key"
    license_key_file = "license_key"
    hash_storage_file = "hash_storage"
    duration_str = "1y"
    user_id = "user_12345"  # Уникальный идентификатор пользователя
    suffix = "txt"  # Используем текстовый формат

    # Генерация ключей
    generate_main_key(main_key_file, suffix)
    generate_license_key(
        f"{main_key_file}.{suffix}",
        license_key_file,
        hash_storage_file,
        duration_str,
        user_id,
        suffix,
    )

    # Проверка лицензии
    check_license(
        f"{license_key_file}.{suffix}", f"{hash_storage_file}.{suffix}", user_id, suffix
    )

    # Генерация RSA ключей
    generate_rsa_keys("public_key.pem", "private_key.pem")

    # Генерация и проверка цифровой подписи
    with open(f"{license_key_file}.{suffix}", "rb") as file:
        license_key_data = file.read()
    generate_signature(license_key_data, "private_key.pem", "signature", suffix)
    verify_signature(license_key_data, f"signature.{suffix}", "public_key.pem", suffix)
