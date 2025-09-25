import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchTransactions, fetchUser } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

interface Transaction {
  transaction_id: string;
  date: string;
  description: string;
  amount: number;
  category: string;
}

interface User {
  name: string;
  age: number;
  credit_score: number;
}

const TransactionsPage: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchParams] = useSearchParams();
  const userId = searchParams.get("userId");
  const { currentUser } = useAuth();

  useEffect(() => {
    const loadData = async () => {
      try {
        // Use a default userId if none provided (for demo purposes)
        const userIdToUse = userId || "user-002";

        const [userData, transactionsData] = await Promise.all([
          fetchUser(userIdToUse),
          fetchTransactions(userIdToUse),
        ]);
        setUser(userData);
        setTransactions(transactionsData);
      } catch (err) {
        setError("Failed to load data.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId]);

  if (loading) {
    return <div className="container mx-auto py-10 px-10">Loading...</div>;
  }

  if (error) {
    return <div className="container mx-auto py-10 px-10">{error}</div>;
  }

  return (
    <div className="container mx-auto py-10 px-10">
      {currentUser && (
        <div className="mb-8">
          <h1 className="text-4xl font-bold">
            Welcome,{" "}
            {currentUser.displayName ||
              currentUser.email?.split("@")[0] ||
              "User"}
          </h1>
          {user && (
            <p className="text-lg text-muted-foreground">
              Age: {user.age} | Credit Score: {user.credit_score}
            </p>
          )}
        </div>
      )}
      <h2 className="text-3xl font-bold mb-4">Transaction History</h2>
      <Table>
        <TableCaption>A list of your recent transactions.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Category</TableHead>
            <TableHead className="text-right">Amount</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((transaction) => (
            <TableRow key={transaction.transaction_id}>
              <TableCell>
                {new Date(transaction.date).toLocaleDateString()}
              </TableCell>
              <TableCell>{transaction.description}</TableCell>
              <TableCell>{transaction.category}</TableCell>
              <TableCell
                className={`text-right ${
                  transaction.amount < 0 ? "text-destructive" : "text-primary"
                }`}
              >
                ${Math.abs(transaction.amount).toFixed(2)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default TransactionsPage;
