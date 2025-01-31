"""
FastAPI application for managing items in an inventory system.

This module provides a RESTful API with the following endpoints:
- GET /: Home page displaying all items
- POST /items/: Create a new item
- PUT /items/{item_id}: Update an existing item
- DELETE /items/{item_id}: Delete an item

The application uses:
- FastAPI for API framework
- SQLAlchemy for database operations
- Jinja2 for template rendering
- Pydantic for data validation
- Custom logging for error tracking

All endpoints include error handling for:
- Database errors
- Validation errors
- General server errors

Data validation ensures:
- Required fields are present
- Price and quantity are non-negative
- Proper data types for all fields
"""
from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, ValidationError
import models
from database import engine, get_db
from logger_config import logger
from typing import Optional

# Initialize database tables using SQLAlchemy models
models.Base.metadata.create_all(bind=engine)

# Create FastAPI application instance
app = FastAPI()
# Configure static files directory for serving CSS, JavaScript, images
app.mount("/static", StaticFiles(directory="static"), name="static")
# Set up Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="templates")

# Define Pydantic model for item validation and data structure
class ItemBase(BaseModel):
    name: str            # Item name field
    description: str     # Item description field
    price: int          # Item price field
    quantity: int       # Item quantity field

# Home page route handler
@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    try:
        logger.info("Accessing home page")
        items = db.query(models.Item).all()
        return templates.TemplateResponse("index.html", {"request": request, "items": items})
    except SQLAlchemyError as e:
        logger.error(f"Database error in home route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error in home route: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/items/")
async def create_item(
    request: Request,
    db: Session = Depends(get_db),
    item: Optional[ItemBase] = None,
    name: str = Form(None),
    description: str = Form(None),
    price: int = Form(None),
    quantity: int = Form(None),
):
    try:
        logger.info("Creating new item")
        
        if request.headers.get('content-type') == 'application/json':
            json_data = await request.json()
            try:
                data = ItemBase(**json_data)
            except ValidationError as e:
                logger.error(f"JSON validation error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid JSON data format"
                )
        else:
            try:
                data = ItemBase(
                    name=name,
                    description=description,
                    price=price,
                    quantity=quantity
                )
            except ValidationError as e:
                logger.error(f"Form validation error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid form data"
                )

        if data.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price cannot be negative"
            )
        
        if data.quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative"
            )
        
        db_item = models.Item(
            name=data.name,
            description=data.description,
            price=data.price,
            quantity=data.quantity
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return {"status": "success", "item": db_item}
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while creating item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error occurred"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while creating item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.put("/items/{item_id}")
async def update_item(
    item_id: int,
    request: Request,
    item: Optional[ItemBase] = None,
    name: str = Form(None),
    description: str = Form(None),
    price: int = Form(None),
    quantity: int = Form(None),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Updating item with id: {item_id}")
        db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )
        
        try:
            if item:
                data = item
            else:
                data = ItemBase(
                    name=name,
                    description=description,
                    price=price,
                    quantity=quantity
                )
        except ValidationError as e:
            logger.error(f"Validation error during update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid data format"
            )

        if data.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Price cannot be negative"
            )
        
        if data.quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity cannot be negative"
            )
        
        db_item.name = data.name
        db_item.description = data.description
        db_item.price = data.price
        db_item.quantity = data.quantity
        
        db.commit()
        db.refresh(db_item)
        return {"status": "success", "item": db_item}
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while updating item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error occurred"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while updating item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Deleting item with id: {item_id}")
        item = db.query(models.Item).filter(models.Item.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )
        
        db.delete(item)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": f"Item {item_id} deleted successfully"}
        )
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while deleting item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error occurred"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while deleting item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
