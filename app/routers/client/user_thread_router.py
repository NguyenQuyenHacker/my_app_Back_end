import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.dependencies import CurrentUserDep
from app.db.database import get_session
from app.schemas.client.user_thread_schema import (
    UserThreadRead,
    UserThreadCreate,
    UserThreadUpdateTitle,
)
from app.services.client.user_thread_service import (
    create_user_thread,
    get_owned_thread,
    get_user_id_from_customer_id,
    list_threads_by_user,
    update_thread_title,
    initialize_new_thread,
    delete_thread_service,
)

router = APIRouter(prefix="/chat/threads", tags=["chat-threads"])


@router.get("", response_model=list[UserThreadRead])
def get_my_threads(
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    return list_threads_by_user(session, user_id)


@router.post("", response_model=UserThreadRead, status_code=status.HTTP_201_CREATED)
def create_thread_mapping(
    data: UserThreadCreate,
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    return create_user_thread(
        session=session,
        user_id=user_id,
        thread_id=data.thread_id,
        title=data.title,
    )


@router.post("/init", response_model=UserThreadRead, status_code=status.HTTP_201_CREATED)
async def init_chat_thread(
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        return await initialize_new_thread(session, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{thread_id}", response_model=UserThreadRead)
def get_my_thread(
    thread_id: uuid.UUID,
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    row = get_owned_thread(session, user_id, thread_id)
    if not row:
        raise HTTPException(status_code=404, detail="Thread not found")

    return row

@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_thread(
    thread_id: uuid.UUID,
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    success = await delete_thread_service(session, user_id, thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")


@router.patch("/{thread_id}", response_model=UserThreadRead)
def rename_my_thread(
    thread_id: uuid.UUID,
    data: UserThreadUpdateTitle,
    current_customer: CurrentUserDep,
    session: Session = Depends(get_session),
):
    user_id = get_user_id_from_customer_id(session, current_customer.customer_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")

    row = update_thread_title(
        session=session,
        user_id=user_id,
        thread_id=thread_id,
        title=data.title,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Thread not found")

    return row