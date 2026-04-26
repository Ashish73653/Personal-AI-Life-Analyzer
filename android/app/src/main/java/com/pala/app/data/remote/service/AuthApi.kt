package com.pala.app.data.remote.service

import com.pala.app.data.remote.dto.ApiEnvelope
import com.pala.app.data.remote.dto.AuthData
import com.pala.app.data.remote.dto.LoginRequest
import com.pala.app.data.remote.dto.RefreshData
import com.pala.app.data.remote.dto.RefreshRequest
import com.pala.app.data.remote.dto.RegisterRequest
import retrofit2.http.Body
import retrofit2.http.POST

interface AuthApi {
    @POST("auth/register")
    suspend fun register(@Body body: RegisterRequest): ApiEnvelope<AuthData>

    @POST("auth/login")
    suspend fun login(@Body body: LoginRequest): ApiEnvelope<AuthData>

    @POST("auth/refresh")
    suspend fun refresh(@Body body: RefreshRequest): ApiEnvelope<RefreshData>
}
