from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class TrendAttributes(BaseModel):
    fit: Optional[str] = None
    silhouette: Optional[str] = None
    fabric: Optional[str] = None
    prints_patterns: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    length: Optional[str] = None
    neckline: Optional[str] = None
    sleeve_style: Optional[str] = None
    details: list[str] = Field(default_factory=list)
    season: Optional[str] = None


class ProductItem(BaseModel):
    url: str
    brand: str
    product_name: str
    category: Optional[str] = None
    price: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list)
    trends: TrendAttributes = Field(default_factory=TrendAttributes)
    scraped_at: str


class BrandReport(BaseModel):
    brand_name: str
    domain: str
    products: list[ProductItem] = Field(default_factory=list)
    dominant_trends: dict = Field(default_factory=dict)
    crawled_at: str


class TrendReport(BaseModel):
    brand_reports: list[BrandReport] = Field(default_factory=list)
    cross_brand_trends: dict = Field(default_factory=dict)
    generated_at: str
    html_output_path: str = ""


class BrandConfig(BaseModel):
    name: str
    domain: str
    new_arrivals_path: str
    categories: list[str] = Field(default_factory=list)
    max_pages: int = 30
