import AlertFeed from "../features/dashboard/AlertFeed";
import RevenueChart from "../features/dashboard/RevenueChart";

export default function Dashboard({ alerts }) {
  return (
    <div className="space-y-6">
      <AlertFeed alerts={alerts} />
      <RevenueChart />
    </div>
  );
}
