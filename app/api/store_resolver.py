#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
店家 ID 解析服務

功能：
1. 將 Google Place ID 轉換為內部整數 store_id
2. 自動建立不存在的店家記錄
3. 支援整數和字串格式的 store_id 輸入
"""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models import Store, db
from typing import Union, Optional
import logging

logger = logging.getLogger(__name__)

def resolve_store_id(store_identifier: Union[str, int], store_name: Optional[str] = None) -> int:
    """
    解析店家識別碼，將 Place ID 或整數轉換為內部 store_id
    
    Args:
        store_identifier: 店家識別碼（可能是整數、數字字串或 Google Place ID）
        store_name: 店家名稱（可選，用於建立新店家時）
    
    Returns:
        int: 內部整數 store_id
        
    Raises:
        ValueError: 當無法解析店家識別碼時
        SQLAlchemyError: 當資料庫操作失敗時
    """
    try:
        # 情況 1: 已經是整數
        if isinstance(store_identifier, int):
            logger.info(f"店家識別碼已經是整數: {store_identifier}")
            return store_identifier
        
        # 情況 2: 數字字串（如 "123"）
        if isinstance(store_identifier, str) and store_identifier.isdigit():
            store_id = int(store_identifier)
            logger.info(f"店家識別碼是數字字串，轉換為整數: {store_id}")
            return store_id
        
        # 情況 3: Google Place ID 字串（如 "ChIJ0boght2rQjQRsH-_buCo3S4"）
        if isinstance(store_identifier, str):
            place_id = store_identifier.strip()
            logger.info(f"嘗試解析 Google Place ID: {place_id}")
            
            # 先查詢是否已存在
            existing_store = db.session.execute(
                select(Store).where(Store.place_id == place_id)
            ).scalars().first()
            
            if existing_store:
                logger.info(f"找到現有店家，store_id: {existing_store.store_id}")
                return existing_store.store_id
            
            # 如果不存在，建立新店家
            logger.info(f"建立新店家記錄，Place ID: {place_id}")
            new_store = Store(
                place_id=place_id,
                store_name=store_name or f"店家_{place_id[:8]}",  # 使用 Place ID 前8位作為預設名稱
                partner_level=0  # 預設為非合作店家
            )
            
            db.session.add(new_store)
            db.session.flush()  # 取得自動遞增的 store_id
            
            logger.info(f"成功建立新店家，store_id: {new_store.store_id}")
            return new_store.store_id
        
        # 其他情況
        raise ValueError(f"不支援的店家識別碼格式: {type(store_identifier)} - {store_identifier}")
        
    except SQLAlchemyError as e:
        logger.error(f"資料庫操作失敗: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f"解析店家識別碼失敗: {e}")
        raise ValueError(f"無法解析店家識別碼: {e}")

def get_store_by_place_id(place_id: str) -> Optional[Store]:
    """
    根據 Google Place ID 查詢店家
    
    Args:
        place_id: Google Place ID
        
    Returns:
        Store 物件或 None
    """
    try:
        store = db.session.execute(
            select(Store).where(Store.place_id == place_id)
        ).scalars().first()
        return store
    except SQLAlchemyError as e:
        logger.error(f"查詢店家失敗: {e}")
        return None

def create_temp_store(place_id: str, store_name: Optional[str] = None) -> Store:
    """
    建立臨時店家記錄
    
    Args:
        place_id: Google Place ID
        store_name: 店家名稱
        
    Returns:
        新建立的 Store 物件
    """
    try:
        store_name = store_name or f"臨時店家_{place_id[:8]}"
        
        new_store = Store(
            place_id=place_id,
            store_name=store_name,
            partner_level=0  # 非合作店家
        )
        
        db.session.add(new_store)
        db.session.flush()
        
        logger.info(f"成功建立臨時店家: {new_store.store_id}")
        return new_store
        
    except SQLAlchemyError as e:
        logger.error(f"建立臨時店家失敗: {e}")
        db.session.rollback()
        raise

def validate_store_id(store_id: Union[str, int]) -> bool:
    """
    驗證店家識別碼格式是否有效
    
    Args:
        store_id: 店家識別碼
        
    Returns:
        bool: 是否有效
    """
    try:
        # 整數
        if isinstance(store_id, int):
            return store_id > 0
        
        # 字串
        if isinstance(store_id, str):
            # 數字字串
            if store_id.isdigit():
                return int(store_id) > 0
            
            # Google Place ID 格式（通常以 ChIJ 開頭）
            if store_id.startswith('ChIJ') and len(store_id) > 10:
                return True
        
        return False
        
    except Exception:
        return False
