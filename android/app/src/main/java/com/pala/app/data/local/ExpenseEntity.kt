package com.pala.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "expenses")
data class ExpenseEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val amount: Double,
    val currency: String,
    val category: String,
    val description: String?,
    val expenseAtIso: String,
    val isSynced: Boolean = false,
)
