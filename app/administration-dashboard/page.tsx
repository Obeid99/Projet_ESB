"use client";

import { Box, Text, Flex, Button, Image } from "@chakra-ui/react";
import { Card, CardBody, CardHeader } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { IoArrowBack, IoBarChart, IoChatbubbles } from "react-icons/io5";
import { useRouter } from "next/navigation";

// Dynamic imports for ESM modules
const Bar = dynamic(() => import("react-chartjs-2").then(mod => mod.Bar), { ssr: false });
const Pie = dynamic(() => import("react-chartjs-2").then(mod => mod.Pie), { ssr: false });

// Dynamically import chart.js/auto to avoid ESM/CommonJS conflict
useEffect(() => {
  (async () => {
    const Chart = (await import("chart.js/auto")).default;
    const { ArcElement } = await import("chart.js");
    Chart.register(ArcElement);
  })();
}, []);


// Images from backend-production/static folder
const imageNames = [
  "bar_stacked_95cc0f42.png",
  "bar_stacked_b56b9397.png",
  "bar_stacked_bf48e2aa.png",
  "bar_total_3879d3da.png",
  "bar_total_5bf2824a.png",
  "bar_total_6ebe98f2.png",
  "pie_510c0198.png",
  "pie_8b239dd5.png",
  "pie_dd17bff4.png",
];

export default function AdministrationDashboardPage() {
  const router = useRouter();
  const [sentimentCounts, setSentimentCounts] = useState({});
  const [intentCounts, setIntentCounts] = useState({});

  useEffect(() => {
    const fetchStats = () => {
      fetch("http://localhost:5000/api/student-stats")
        .then((res) => res.json())
        .then((stats) => {
          setSentimentCounts(stats.sentiment || {});
          setIntentCounts(stats.intent || {});
        });
    };

    fetchStats(); // initial fetch
    const interval = setInterval(fetchStats, 5000); // fetch every 5 seconds

    return () => clearInterval(interval); // cleanup on unmount
  }, []);

  const sentimentChart = {
    labels: Object.keys(sentimentCounts),
    datasets: [
      {
        label: "Sentiment",
        data: Object.values(sentimentCounts),
        backgroundColor: ["#ec534bff", "#5b5555ff", "#38A169", "#3182CE"],
      },
    ],
  };

  const intentChart = {
    labels: Object.keys(intentCounts),
    datasets: [
      {
        label: "Intent",
        data: Object.values(intentCounts),
        backgroundColor: ["#3182CE", "#38A169", "#E53E3E", "#ECC94B", "#805AD5"],
      },
    ],
  };

  return (
    <Flex w="100vw" h="100vh">
      {/* Sidebar */}
      <Flex
        direction="column"
        w="250px"
        bg="red.500"
        color="white"
        p="20px"
        justifyContent="flex-start"
        alignItems="center"
      >
        <Box mb="9" display="flex" flexDirection="column" alignItems="center" w="100%">
          <Image
            src="/img/esb.png"
            boxSize="120px"
            borderRadius="full"
            mb="4"
            border="3px solid white"
          />
        </Box>
        <Button
          leftIcon={<IoArrowBack size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/welcome')}
        >
          Back
        </Button>
        <Button
          leftIcon={<IoBarChart size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/administration-dashboard')}
        >
          Dashboard
        </Button>
        <Button
          leftIcon={<IoChatbubbles size={20} color="#e53e3e" />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          mb="10px"
          onClick={() => router.push('/administration-chatbot')}
        >
          Chatbot
        </Button>
      </Flex>

      {/* Dashboard Charts & Images */}
      <Flex flex="1" direction="column" alignItems="center" justifyContent="center" bg="#f8fafc" p="40px" gap={6}>
        <Text fontSize="2xl" fontWeight="bold" mb="24px" color="#2d3748" textAlign="center">
          Student Sentiment & Intent Dashboard
        </Text>
        <Flex direction={["column", "row"]} alignItems="stretch" justifyContent="center" w="100%" maxW="1100px" gap={8}>
          <Card flex="1" minW="320px" maxW="600px" boxShadow="lg" borderRadius="lg" bg="#fff" border="2px solid #E53E3E" display="flex" flexDirection="column" alignItems="center">
            <CardHeader bg="#E53E3E" color="white" borderTopLeftRadius="lg" borderTopRightRadius="lg" textAlign="center" w="100%">
              <Text fontWeight="bold" fontSize="lg">Sentiment Distribution</Text>
            </CardHeader>
            <CardBody w="100%" display="flex" flexDirection="column" alignItems="center" justifyContent="center">
              <Pie data={sentimentChart} />
            </CardBody>
          </Card>
          <Card flex="1" minW="320px" maxW="600px" boxShadow="lg" borderRadius="lg" bg="#fff" border="2px solid #E53E3E" display="flex" flexDirection="column" alignItems="center">
            <CardHeader bg="#E53E3E" color="white" borderTopLeftRadius="lg" borderTopRightRadius="lg" textAlign="center" w="100%">
              <Text fontWeight="bold" fontSize="lg">Intent Distribution</Text>
            </CardHeader>
            <CardBody w="100%" display="flex" flexDirection="column" alignItems="center" justifyContent="center">
              <Bar
                data={intentChart}
                options={{ plugins: { legend: { display: false } } }}
              />
              <Box mt={6} w="100%" textAlign="left">
                <Text fontWeight="bold" mb={2} color="#E53E3E" fontSize="md">Intents:</Text>
                <Box display="grid" gridTemplateColumns="repeat(2, 1fr)" gap={2} ml={4} fontSize="0.95em">
                  {Object.keys(intentCounts).map((intent, idx) => (
                    <Box key={intent} display="flex" alignItems="center" gap={2} mb={2} fontWeight={500} color="#2d3748">
                      <span style={{ display: 'inline-block', width: '16px', height: '16px', borderRadius: '4px', background: intentChart.datasets[0].backgroundColor[idx % intentChart.datasets[0].backgroundColor.length], border: '1px solid #ccc' }}></span>
                      <span>{intent}</span>
                    </Box>
                  ))}
                </Box>
              </Box>
            </CardBody>
          </Card>
        </Flex>
      </Flex>
    </Flex>
  );
}
